import logging
from datetime import datetime
from typing import List, Dict, Any

import sqlalchemy as sa
from sqlalchemy import event, Table, and_, inspect
from sqlalchemy.orm import (
    Session,
    ORMExecuteState,
    with_loader_criteria,
    RelationshipProperty,
    Mapper,
    declared_attr,
    MANYTOMANY,
    ONETOMANY,
)
from sqlalchemy.orm.strategies import LazyLoader
from sqlalchemy.orm.util import _ORMJoin

soft_delete_mixin_mappers: List[sa.orm.Mapper] = []  # noqa: FA100


class SoftDeleteMixin:
    @declared_attr
    def __mapper_cls__(cls):
        def map_(cls, *arg: Any, **kw: Any):
            mp = sa.orm.mapper(cls, *arg, **kw)

            soft_delete_mixin_mappers.append(mp)

            return mp

        return map_

    deleted_at = sa.Column(sa.DateTime(timezone=False), nullable=True)

    def delete(self, deleted_at: datetime = None):
        self.deleted_at = deleted_at or datetime.now()

    def restore(self):
        self.deleted_at = None


def exclude_deleted(join_condition, table):
    if isinstance(table, Table):
        table = table.c
    return and_(join_condition, table.deleted_at.is_(None))


def process_joinedload(execute_state: ORMExecuteState):
    rels: List[RelationshipProperty] = execute_state.bind_mapper.relationships

    def _get_table(right):
        if isinstance(right, Table):
            return right

        return right.element

    joins: Dict[Table, _ORMJoin] = {  # noqa: FA100
        _get_table(join.right): join for join in execute_state.statement.froms if isinstance(join, _ORMJoin)
    }
    if joins:
        for rel in rels:
            # noinspection PyTypeChecker
            rel_mapper: Mapper = rel.entity
            if rel_mapper.local_table in joins and issubclass(rel_mapper.class_, SoftDeleteMixin):
                execute_state.statement = execute_state.statement.options(
                    with_loader_criteria(rel_mapper.entity, lambda cls: cls.deleted_at.is_(None), include_aliases=True)
                )


@event.listens_for(Session, "do_orm_execute")
def before_compile(execute_state: ORMExecuteState) -> None:
    include_deleted = execute_state.execution_options.get("include_deleted", False)
    soft_delete_skip_modification = (
        execute_state.is_relationship_load
        and execute_state.loader_strategy_path.prop.info.get("soft_delete_skip_modification", False)
    )
    if include_deleted:
        return

    if soft_delete_skip_modification:
        return

    if not isinstance(execute_state.statement, sa.sql.Select):
        return

    if not execute_state.is_relationship_load and execute_state.all_mappers:
        for column in execute_state.statement.column_descriptions:
            entity = column["entity"]
            if entity is None:
                continue

            inspector = inspect(column["entity"])
            mapper = getattr(inspector, "mapper", None)
            if mapper and issubclass(mapper.class_, SoftDeleteMixin):
                execute_state.statement = execute_state.statement.where(
                    entity.deleted_at.is_(None),
                )

    else:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(SoftDeleteMixin, lambda cls: cls.deleted_at.is_(None), include_aliases=True)
        )


@event.listens_for(Mapper, "after_configured")
def after_configured():
    if not soft_delete_mixin_mappers:
        return

    registry = soft_delete_mixin_mappers[0].class_.registry
    registry_map = {mapper.class_.__tablename__: mapper for mapper in registry.mappers}

    for mapper in registry.mappers:
        for relationship in mapper.relationships:
            if not (is_softdelte := issubclass(relationship.mapper.class_, SoftDeleteMixin)):
                continue

            re_setup_join_conditions = False

            if relationship.info.get("soft_delete_skip_modification", None):
                continue

            if relationship.direction == ONETOMANY:
                # по идеи этот случай должен обрабатываться через with_loader_criteria
                # но оно заходит в process_joinedload и там не хватает парочки условий
                re_setup_join_conditions = True
                relationship.primaryjoin = exclude_deleted(relationship.primaryjoin, relationship.entity.class_)

            if relationship.direction == MANYTOMANY:
                if relationship.secondary is None:
                    continue

                if not isinstance(relationship.secondary, Table):
                    logging.getLogger("softdelete-mixin").warning(
                        f"Filtering of deleted objects was skipped for relation {relationship}: "
                        f"not correct secondary table. To auto enable softdelete, "
                        f"use usual secondary table "
                        f"or apply filtering condition `deleted_at == None` by yourself "
                        f'(like `secondary="join(M2MTable,TargetTable, '
                        f'and_(M2MTable.target_id == TargetTable.id,M2MTable.deleted_at == None))"). '
                        f'To supress this warning specify param `info={{"soft_delete_skip_modification": True}}`'
                        f" for relationship"
                    )
                    continue

                secondary_mapper = registry_map[relationship.secondary.name]

                if issubclass(relationship.entity.class_, SoftDeleteMixin):
                    re_setup_join_conditions = True
                    relationship.secondaryjoin = exclude_deleted(relationship.secondaryjoin, relationship.entity.class_)

                if issubclass(secondary_mapper.class_, SoftDeleteMixin):
                    re_setup_join_conditions = True
                    relationship.primaryjoin = exclude_deleted(relationship.primaryjoin, relationship.secondary)

                    if isinstance(relationship.strategy, LazyLoader):
                        relationship.strategy._lazywhere = exclude_deleted(
                            relationship.strategy._lazywhere, relationship.secondary
                        )

            if re_setup_join_conditions:
                relationship._setup_join_conditions()
