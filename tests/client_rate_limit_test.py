import responses

from gocardless_pro import Client

access_token = 'access-token-xyz'
client = Client(access_token=access_token, base_url='http://example.com')


@responses.activate
def test_client_rate_limit_exposes_attributes():
    responses.add(responses.GET, 'http://example.com/customers',
                  body='{"customers": []}',
                  headers={'ratelimit-limit': '1000',
                           'ratelimit-remaining': '163',
                           'ratelimit-reset': 'Thu, 03 May 2018 16:00:00 GMT'})
    client.customers.list()
    assert client.rate_limit.limit == 1000
    assert client.rate_limit.remaining == 163
    assert client.rate_limit.reset == 'Thu, 03 May 2018 16:00:00 GMT'
