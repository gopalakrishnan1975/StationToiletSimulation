"""Server-side client: URL and token come from deployment secrets, never public inputs."""
from urllib.parse import urlparse
import requests
from .data import validate_calls


def fetch_calls(base_url,token,station,platform,service_date):
    parsed=urlparse(base_url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('DATA_API_BASE must be an HTTPS origin/base path without credentials or query')
    try:
        response=requests.get(base_url.rstrip('/')+'/v1/data/train-calls',
                              params={'station':station,'platform':platform,'service_date':str(service_date)},
                              headers={'Authorization':'Bearer '+token},timeout=(5,15),allow_redirects=False,stream=True)
        try:
            if response.status_code!=200:
                raise ValueError(f'Data API returned HTTP {response.status_code}')
            chunks=[]; total=0
            for chunk in response.iter_content(65536):
                total+=len(chunk)
                if total>1_000_000:
                    raise ValueError('Data API response exceeds 1 MB')
                chunks.append(chunk)
        finally:
            response.close()
        import json
        payload=json.loads(b''.join(chunks))
        if payload.get('schema_version')!='1.0':
            raise ValueError('Unsupported data schema version')
        return validate_calls(payload['records'])
    except requests.RequestException:
        raise ValueError('Data API could not be reached; check service configuration') from None
    except (KeyError,TypeError):
        raise ValueError('Data API response does not match the records contract') from None
