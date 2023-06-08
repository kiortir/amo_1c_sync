from amocrm_api_client import (AmoCrmApiClient, AmoCrmApiClientConfig,
                               create_amocrm_api_client)
from amocrm_api_client.token_provider import StandardTokenProviderFactory
from amocrm_api_client.token_provider.impl.standard import \
    StandardTokenProvider
from amocrm_api_client.token_provider.impl.standard.token_storage import \
    RedisTokenStorageImpl

from redis_client import redis_client
from settings import amo_settings

token_provider_factory = StandardTokenProviderFactory()
token_provider: "StandardTokenProvider" = token_provider_factory.get_instance(
    settings=amo_settings.dict(),
    token_storage_class=RedisTokenStorageImpl,
    redis_client=redis_client,
)

amo_client: AmoCrmApiClient = create_amocrm_api_client(
    token_provider=token_provider,
    config=AmoCrmApiClientConfig(base_url=amo_settings.base_url),
)

# r = token_provider()
