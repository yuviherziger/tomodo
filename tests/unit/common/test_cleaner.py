import logging
from contextlib import ExitStack
from typing import List
from unittest.mock import Mock, patch, MagicMock

from _pytest.logging import LogCaptureFixture
from docker.models.containers import Container

from tomodo import Cleaner


class TestCleaner:

    @staticmethod
    def test_stop_deployment_standalone(cleaner_client: Mock, standalone_container: Container,
                                        caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        cleaner_client.containers.list.return_value = [standalone_container]
        cleaner_client.containers.get.return_value = standalone_container
        container_id = standalone_container.short_id
        cleaner = Cleaner()
        with patch.object(standalone_container, "stop") as mock_stop:
            with caplog.at_level(logging.INFO):
                cleaner.stop_deployment(name=depl_name)
                mock_stop.assert_called_once()
                assert f"Container {container_id} stopped" in caplog.text

    @staticmethod
    def test_stop_deployment_stopped_standalone(cleaner_client: Mock, standalone_container: Container,
                                                caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        container = Container(attrs={**standalone_container.attrs, "State": "stopped"})
        cleaner_client.containers.list.return_value = [container]
        cleaner_client.containers.get.return_value = container
        container_id = container.short_id
        cleaner = Cleaner()
        with patch.object(container, "stop") as mock_stop:
            with caplog.at_level(logging.INFO):
                cleaner.stop_deployment(name=depl_name)
                mock_stop.assert_not_called()
                assert f"Container {container_id} isn't running" in caplog.text

    @staticmethod
    def test_stop_deployment_replica_set(cleaner_client: Mock, replica_set_containers: List[Container],
                                         caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        cleaner_client.containers.list.return_value = replica_set_containers
        cleaner_client.containers.get.side_effect = replica_set_containers

        cleaner = Cleaner()

        with caplog.at_level(logging.INFO):
            with ExitStack() as stack:
                mocks = [stack.enter_context(patch.object(container, "stop")) for container in replica_set_containers]
                container_ids = [container.short_id for container in replica_set_containers]
                cleaner.stop_deployment(name=depl_name)
            for mock_stop in mocks:
                mock_stop.assert_called_once()

        for container_id in container_ids:
            assert f"Container {container_id} stopped" in caplog.text

    @staticmethod
    def test_stop_deployment_sharded_cluster(cleaner_client: Mock, sharded_cluster_containers: List[Container],
                                             caplog: LogCaptureFixture):
        depl_name = "unit-test-sc"
        cleaner_client.containers.list.return_value = sharded_cluster_containers
        cleaner_client.containers.get.side_effect = sharded_cluster_containers

        cleaner = Cleaner()

        with caplog.at_level(logging.INFO):
            with ExitStack() as stack:
                mocks = [stack.enter_context(patch.object(container, "stop")) for container in
                         sharded_cluster_containers]
                container_ids = [container.short_id for container in sharded_cluster_containers]
                cleaner.stop_deployment(name=depl_name)
            for mock_stop in mocks:
                mock_stop.assert_called_once()

        for container_id in container_ids:
            assert f"Container {container_id} stopped" in caplog.text

    @staticmethod
    @patch("shutil.rmtree")
    @patch("os.path.exists")
    def test_delete_deployment_standalone(mock_exists: MagicMock, mock_rmtree: MagicMock,
                                          cleaner_client: Mock, standalone_container: Container,
                                          caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        mock_exists.side_effect = lambda x: True
        cleaner_client.containers.list.return_value = [standalone_container]
        cleaner_client.containers.get.return_value = standalone_container
        container_id = standalone_container.short_id
        cleaner = Cleaner()
        with patch.object(standalone_container, "remove") as mock_remove:
            cleaner.delete_deployment(name=depl_name)
            mock_remove.assert_called_once()
            mock_exists.assert_called_once()
            mock_rmtree.assert_called_once()

    @staticmethod
    @patch("shutil.rmtree")
    @patch("os.path.exists")
    def test_delete_deployment_standalone_with_shutil_exception(mock_exists: MagicMock, mock_rmtree: MagicMock,
                                                                cleaner_client: Mock, standalone_container: Container,
                                                                caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        data_dir = f"/var/tmp/tomodo/data/{depl_name}-db"
        mock_exists.side_effect = lambda x: True
        mock_rmtree.side_effect = OSError("Permission denied")
        cleaner_client.containers.list.return_value = [standalone_container]
        cleaner_client.containers.get.return_value = standalone_container

        cleaner = Cleaner()
        with caplog.at_level(logging.INFO):
            with patch.object(standalone_container, "remove") as mock_remove:
                cleaner.delete_deployment(name=depl_name)
                mock_remove.assert_called_once()
                mock_exists.assert_called_once()
                mock_rmtree.assert_called_once()
                assert f"An error occurred while trying to remove '{data_dir}" in caplog.text

    @staticmethod
    @patch("shutil.rmtree")
    @patch("os.path.exists")
    def test_delete_deployment_standalone_nonexistent_path(mock_exists: MagicMock, mock_rmtree: MagicMock,
                                                           cleaner_client: Mock, standalone_container: Container,
                                                           caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        mock_exists.side_effect = lambda x: False
        cleaner_client.containers.list.return_value = [standalone_container]
        cleaner_client.containers.get.return_value = standalone_container
        container_id = standalone_container.short_id
        cleaner = Cleaner()
        with patch.object(standalone_container, "remove") as mock_remove:
            cleaner.delete_deployment(name=depl_name)
            mock_remove.assert_called_once()
            mock_rmtree.assert_not_called()
            mock_exists.assert_called_once()

    @staticmethod
    @patch("shutil.rmtree")
    @patch("os.path.exists")
    def test_delete_deployment_replica_set(mock_exists: MagicMock, mock_rmtree: MagicMock,
                                           cleaner_client: Mock, replica_set_containers: List[Container],
                                           caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        cleaner_client.containers.list.return_value = replica_set_containers
        cleaner_client.containers.get.side_effect = replica_set_containers

        cleaner = Cleaner()

        with ExitStack() as stack:
            mocks = [stack.enter_context(patch.object(container, "remove")) for container in replica_set_containers]
            container_ids = [container.short_id for container in replica_set_containers]
            cleaner.delete_deployment(name=depl_name)
        for mock_remove in mocks:
            mock_remove.assert_called_once()

    @staticmethod
    @patch("shutil.rmtree")
    @patch("os.path.exists")
    def test_delete_deployment_sharded_cluster(mock_exists: MagicMock, mock_rmtree: MagicMock,
                                               cleaner_client: Mock, sharded_cluster_containers: List[Container],
                                               caplog: LogCaptureFixture):
        depl_name = "unit-test-sc"
        cleaner_client.containers.list.return_value = sharded_cluster_containers
        cleaner_client.containers.get.side_effect = sharded_cluster_containers

        cleaner = Cleaner()

        with ExitStack() as stack:
            mocks = [stack.enter_context(patch.object(container, "remove")) for container in sharded_cluster_containers]
            container_ids = [container.short_id for container in sharded_cluster_containers]
            cleaner.delete_deployment(name=depl_name)
        for mock_remove in mocks:
            mock_remove.assert_called_once()

    @staticmethod
    @patch("shutil.rmtree")
    @patch("os.path.exists")
    def test_delete_all_deployments(mock_exists: MagicMock, mock_rmtree: MagicMock,
                                    cleaner_client: Mock, standalone_container: Container,
                                    caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        mock_exists.side_effect = lambda x: True
        cleaner_client.containers.list.return_value = [standalone_container]
        cleaner_client.containers.get.return_value = standalone_container
        container_id = standalone_container.short_id
        cleaner = Cleaner()
        with patch.object(standalone_container, "remove") as mock_remove:
            cleaner.delete_all_deployments()
            mock_remove.assert_called_once()
            mock_exists.assert_called_once()
            mock_rmtree.assert_called_once()

    @staticmethod
    def test_stop_all_deployments(cleaner_client: Mock, standalone_container: Container,
                                  caplog: LogCaptureFixture):
        depl_name = "unit-test-sa"
        cleaner_client.containers.list.return_value = [standalone_container]
        cleaner_client.containers.get.return_value = standalone_container
        container_id = standalone_container.short_id
        cleaner = Cleaner()
        with patch.object(standalone_container, "stop") as mock_stop:
            with caplog.at_level(logging.INFO):
                cleaner.stop_all_deployments()
                mock_stop.assert_called_once()
                assert f"Container {container_id} stopped" in caplog.text
