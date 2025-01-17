# Copyright 2019-2021 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)
""" Test the cray/cfs/operator/v1/session_events.py module """
import logging
from unittest.mock import patch, Mock

from kubernetes.client import BatchV1Api
from kubernetes.client.rest import ApiException

from kubernetes import config
config.load_incluster_config = Mock()
config.load_kube_config = Mock()

from cray.cfs.operator.events import CFSSessionController  # pylint: disable=E402
from cray.cfs.operator.events.job_events import CFSJobMonitor


def test__handle_added(create_event_v2):
    """ Test the cray.cfs.operator.events.session_events._handle_added method """
    with patch.object(CFSSessionController, '_create_k8s_job') as cfs_job:
        with patch('cray.cfs.operator.cfs.sessions.update_session_status'):
            with patch.object(CFSJobMonitor, 'add_session'):
                conn = CFSSessionController({'RESOURCE_NAMESPACE': 'foo'})
                conn._handle_event(create_event_v2, Mock())
                cfs_job.assert_called_once()


def test__handle_deleted(delete_event):
    """ Test the cray.cfs.operator.events.session_events._handle_deleted method """
    with patch.object(BatchV1Api, 'delete_namespaced_job') as delete:
        conn = CFSSessionController({'RESOURCE_NAMESPACE': 'foo'})
        conn._handle_event(delete_event, Mock())
        delete.assert_called_once()


def test__handle_deleted_failed(delete_event):
    """ Test the cray.cfs.operator.events.session_events._handle_deleted method """
    with patch.object(BatchV1Api, 'delete_namespaced_job', side_effect=ApiException()) as delete:
        conn = CFSSessionController({'RESOURCE_NAMESPACE': 'foo'})
        conn._handle_event(delete_event, Mock())
        delete.assert_called_once()


def test__create_k8s_job(session_data_v2, job_id, k8s_api_response, config_response, aee_env,
                         mock_options, caplog):
    """ Test the cray.cfs.operator/events/session_events._create_k8s_job method """
    caplog.set_level(logging.DEBUG)
    # Successful response
    with patch.object(BatchV1Api, 'create_namespaced_job', return_value=k8s_api_response()):
        with patch('cray.cfs.operator.events.session_events.get_configuration',
                   return_value=config_response):
            with patch('cray.cfs.operator.events.session_events.options',
                       mock_options):
                conn = CFSSessionController(aee_env)
                conn._create_k8s_job(session_data_v2, job_id)
                BatchV1Api.create_namespaced_job.assert_called_once()
    for record in caplog.records:
        assert 'Job request created' in record.message

    # Some other API error
    caplog.clear()
    with patch.object(BatchV1Api, 'create_namespaced_job', side_effect=ApiException(status=500)):
        with patch('cray.cfs.operator.events.session_events.get_configuration',
                   return_value=config_response):
            with patch('cray.cfs.operator.events.session_events.options',
                       mock_options):
                conn = CFSSessionController(aee_env)
                conn._create_k8s_job(session_data_v2, job_id)
                BatchV1Api.create_namespaced_job.assert_called_once()
    for record in caplog.records:
        assert 'Unable to create Job' in record.message


def test__v1_create_k8s_job(session_data_v1, job_id,
                            k8s_api_response, aee_env, mock_options, caplog):
    """ Test the cray.cfs.operator/events/session_events._create_k8s_job method """
    caplog.set_level(logging.DEBUG)
    # Successful response
    with patch.object(BatchV1Api, 'create_namespaced_job', return_value=k8s_api_response()):
        with patch('cray.cfs.operator.events.session_events.options',
                   mock_options):
            conn = CFSSessionController(aee_env)
            conn._create_k8s_job(session_data_v1, job_id)
            BatchV1Api.create_namespaced_job.assert_called_once()
    for record in caplog.records:
        assert 'Job request created' in record.message

    # Some other API error
    caplog.clear()
    with patch.object(BatchV1Api, 'create_namespaced_job', side_effect=ApiException(status=500)):
        with patch('cray.cfs.operator.events.session_events.options',
                   mock_options):
            conn = CFSSessionController(aee_env)
            conn._create_k8s_job(session_data_v1, job_id)
            BatchV1Api.create_namespaced_job.assert_called_once()
    for record in caplog.records:
        assert 'Unable to create Job' in record.message


def test__create_k8s_job_image_customization(session_data_v2, job_id, k8s_api_response,
                                             config_response, aee_env, mock_options, caplog):
    """ Test the cray.cfs.operator/events/session_events._create_k8s_job method when target/def = image """
    caplog.set_level(logging.DEBUG)
    # Successful response
    session_data_v2['target']['definition'] = 'image'
    with patch.object(BatchV1Api, 'create_namespaced_job', return_value=k8s_api_response()):
        with patch('cray.cfs.operator.events.session_events.get_configuration',
                   return_value=config_response):
            with patch('cray.cfs.operator.events.session_events.options',
                       mock_options):
                conn = CFSSessionController(aee_env)
                conn._create_k8s_job(session_data_v2, job_id)
                BatchV1Api.create_namespaced_job.assert_called_once()
    for record in caplog.records:
        assert 'Job request created' in record.message
