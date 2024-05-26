from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    facebook_page_id: str = '613101857342580'
    facebook_page_access_token: str = 'EAAM4sCOqR98BO8ceLdgSUbGTtl4ATfxoAOAMrLcPZAWm0ptNTPZCYPz1OTTThZB5fZAxkUiIX76oYEOE8ZAfgknDnIDghIY2oF5ZC6fcURFPBWWyeYXoocXAXCbEyXXhhZCGZAe3ZAZAwGVHAKZBxW0l59PNHnFh5dH8biL9yvFFFcq8DBQ7LLNNXQcJoa2krBbmjGE1mZAUxyf1jTZAKBlMZD'
    facebook_verify_token: str = 'rin080902'

    class Config:
        env_file = '.env'

settings = Settings()
