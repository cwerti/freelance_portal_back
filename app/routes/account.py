import fastapi
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from models.general import User

account = fastapi.APIRouter()


@account.get("/user-info", response_model=UserFullInfoOut)
async def get_user_info(
        session: AsyncSession = fastapi.Depends(db_async_session),
        author: UserInfo = fastapi.Depends(user_info_dep),
        fetcher: UserAccountFetcher = fastapi.Depends(user_account_fetcher_dep),
):
    """
    Получаем информацию о самом себе
    """
    data = await fetcher.get(session, author.id)
    return ORJSONResponse(data)
