import logging

import pkg_resources
import pytz

from airflow_monitor.data_fetchers import data_fetcher_factory

from dbnd._core.utils.timezone import utcnow
from dbnd._vendor import pendulum
from dbnd.api.shared_schemas.airflow_monitor import (
    AirflowServerInfo,
    airflow_server_info_schema,
)


logger = logging.getLogger(__name__)


class AirflowInstanceDetails(object):
    def __init__(self, config, since, server_info, fetcher):
        self.config = config
        self.since = since
        self.airflow_server_info = server_info
        self.data_fetcher = fetcher
        self.exception_traceback = None


def create_airflow_server_info(airflow_url, interval):
    airflow_server_info = AirflowServerInfo(
        base_url=airflow_url,
        monitor_status="Running",
        airflow_monitor_version=pkg_resources.get_distribution(
            "dbnd_airflow_monitor"
        ).version,
        sync_interval=interval,
    )

    return airflow_server_info


def get_sync_times_from_api(api_client, airflow_server_info):
    """ Update airflow server info with sync times retrieved from API """
    response = api_client.api_request(
        "airflow_monitor/get_synced_time_frame",
        {},
        "GET",
        query={"base_url": airflow_server_info.base_url},
    )
    fetched_server_info = airflow_server_info_schema.load(response).data
    airflow_server_info.synced_from = fetched_server_info.synced_from
    airflow_server_info.synced_to = fetched_server_info.synced_to
    airflow_server_info.last_sync_time = fetched_server_info.last_sync_time


def calculate_since_value(
    since_now, since, sync_history, history_only, api_client, airflow_server_info
):
    if since_now:
        final_since_value = utcnow()
    elif since:
        final_since_value = pendulum.parse(since, tz=pytz.UTC)
    elif sync_history or history_only:
        final_since_value = pendulum.datetime.min
    else:
        # Default mode
        try:
            get_sync_times_from_api(api_client, airflow_server_info)
            final_since_value = airflow_server_info.synced_to
            logger.info(
                "Resuming sync from latest stop at: %s",
                airflow_server_info.last_sync_time,
            )
        except Exception:
            logger.info(
                "Could not locate latest sync stop. Starting Airflow Monitor syncing from the beginning."
            )
            final_since_value = pendulum.datetime.min

    return final_since_value


def create_instance_details_first_time(
    monitor_args, airflow_config, configs_fetched, api_client
):
    airflow_instance_details = []
    for fetch_config in configs_fetched:
        airflow_server_info = create_airflow_server_info(
            fetch_config.base_url, airflow_config.interval
        )
        since_value = calculate_since_value(
            monitor_args.since_now,
            monitor_args.since,
            monitor_args.sync_history,
            monitor_args.history_only,
            api_client,
            airflow_server_info,
        )
        airflow_instance_details.append(
            AirflowInstanceDetails(
                fetch_config,
                since_value,
                airflow_server_info,
                data_fetcher_factory(fetch_config),
            )
        )
    return airflow_instance_details


def create_airflow_instance_details_with_existing(
    monitor_args, airflow_config, api_client, configs_fetched, existing_details
):
    airflow_instance_details = []
    for fetch_config in configs_fetched:
        was_found = False
        for existing_detail in existing_details:
            if existing_detail.config.url == fetch_config.url:
                airflow_instance_details.append(existing_detail)
                was_found = True
                break
        if not was_found:
            airflow_server_info = create_airflow_server_info(
                fetch_config.base_url, airflow_config.interval
            )
            since_value = calculate_since_value(
                monitor_args.since_now,
                monitor_args.since,
                monitor_args.sync_history,
                monitor_args.history_only,
                api_client,
                airflow_server_info,
            )
            airflow_instance_details.append(
                AirflowInstanceDetails(
                    fetch_config,
                    since_value,
                    airflow_server_info,
                    data_fetcher_factory(fetch_config),
                )
            )

    return airflow_instance_details
