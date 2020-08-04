# Copyright (C) NIWA & British Crown (Met Office) & Contributors.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for the ``data_store_mgr`` module and its objects and functions."""

import logging

import pytest

import cylc.uiserver.data_store_mgr as data_store_mgr_module
from cylc.uiserver.data_store_mgr import DataStoreMgr
from .conftest import AsyncClientFixture


@pytest.mark.asyncio
async def test_entire_workflow_update(
        async_client: AsyncClientFixture,
        data_store_mgr: DataStoreMgr,
        make_entire_workflow
):
    """Test that ``entire_workflow_update`` is executed successfully."""
    w_id = 'workflow_id'
    entire_workflow = make_entire_workflow(f'{w_id}')
    async_client.will_return(entire_workflow.SerializeToString())

    # Set the client used by our test workflow.
    data_store_mgr.workflows_mgr.active[w_id] = {
        'req_client': async_client
    }

    # Call the entire_workflow_update function.
    # This should use the client defined above (``async_client``) when
    # calling ``workflow_request``.
    await data_store_mgr.entire_workflow_update()

    # The ``DataStoreMgr`` sets the workflow data retrieved in its
    # own ``.data`` dictionary, which will contain Protobuf message
    # objects.
    w_id_data = data_store_mgr.data[w_id]

    # If everything went OK, we should have the Protobuf object
    # de-serialized and added to the ``DataStoreMgr.data``
    # (the workflow ID is its key).
    assert entire_workflow.workflow.id == w_id_data['workflow'].id


@pytest.mark.asyncio
async def test_entire_workflow_update_gather_error(
        async_client: AsyncClientFixture,
        data_store_mgr: DataStoreMgr,
        mocker
):
    """
    Test that if ``asyncio.gather`` in ``entire_workflow_update``
    has a coroutine raising an error, it will handle the error correctly.
    """
    # The ``AsyncClient`` will raise an error. This will happen when
    # ``workflow_request`` is called via ``asyncio.gather``, which
    # would be raised if ``return_exceptions`` is not given.
    #
    # This test wants to confirm this is not raised, but instead the
    # error is returned, so that we can inspect, log, etc.
    error_type = ValueError
    async_client.will_return(error_type)

    # Set the client used by our test workflow.
    data_store_mgr.workflows_mgr.active['workflow_id'] = {
        'req_client': async_client
    }

    # Call the entire_workflow_update function.
    # This should use the client defined above (``async_client``) when
    # calling ``workflow_request``.
    logger = logging.getLogger(data_store_mgr_module.__name__)
    mocked_exception_function = mocker.patch.object(logger, 'exception')
    await data_store_mgr.entire_workflow_update()
    mocked_exception_function.assert_called_once()
    assert mocked_exception_function.call_args[1][
               'exc_info'].__class__ == error_type
