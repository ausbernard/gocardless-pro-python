from unittest.mock import MagicMock, call

from gocardless_pro.paginator import Paginator


def make_page(records, after=None):
    page = MagicMock()
    page.records = records
    page.after = after
    return page


def make_service(*pages):
    service = MagicMock()
    service.list.side_effect = list(pages)
    return service


def test_single_page_yields_all_records():
    page = make_page(['a', 'b', 'c'])
    service = make_service(page)

    result = list(Paginator(service, {}))

    assert result == ['a', 'b', 'c']
    assert service.list.call_count == 1


def test_multiple_pages_follows_cursor():
    page1 = make_page(['a', 'b'], after='cursor-1')
    page2 = make_page(['c', 'd'], after='cursor-2')
    page3 = make_page(['e'], after=None)
    service = make_service(page1, page2, page3)

    result = list(Paginator(service, {}))

    assert result == ['a', 'b', 'c', 'd', 'e']
    assert service.list.call_count == 3


def test_after_cursor_passed_to_next_fetch():
    page1 = make_page(['a'], after='cursor-xyz')
    page2 = make_page(['b'], after=None)
    service = make_service(page1, page2)

    list(Paginator(service, {}))

    assert service.list.call_args_list == [
        call(params={}),
        call(params={'after': 'cursor-xyz'}),
    ]


def test_empty_page_yields_nothing():
    page = make_page([], after=None)
    service = make_service(page)

    result = list(Paginator(service, {}))

    assert result == []


def test_params_passed_to_service():
    page = make_page([], after=None)
    service = make_service(page)

    list(Paginator(service, {'status': 'active', 'limit': 50}))

    service.list.assert_called_once_with(params={'status': 'active', 'limit': 50})


def test_identity_params_passed_to_service():
    page = make_page([], after=None)
    service = make_service(page)

    list(Paginator(service, {}, identity_params={'creditor_id': 'CR123'}))

    service.list.assert_called_once_with(creditor_id='CR123', params={})


def test_original_params_not_mutated():
    page1 = make_page(['a'], after='cursor-1')
    page2 = make_page(['b'], after=None)
    service = make_service(page1, page2)
    original_params = {'status': 'active'}

    list(Paginator(service, original_params))

    assert original_params == {'status': 'active'}
