import logging
import asyncio
import socket
from typing import Optional
import aiohttp
import async_timeout
from datetime import datetime, timedelta
import pickle
import os

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class YaleDoormanViaSmarthubApiClient:
    def __init__(
        self, username: str, password: str, session: aiohttp.ClientSession
    ) -> None:
        self._username = username
        self._password = password
        self._session = session
    
    async def async_login(self):
        try:
            if self._access_token is not None:
                if self._token_expires > datetime.now():
                    return True
                else:
                    # Refresh token
                    # Left as an exercise to the reader :)
                    pass

        except Exception as exception:
            pass
        
        with open(os.path.join(os.path.dirname(__file__),"hub.login"), 'rb') as f:
            hub_login = pickle.load(f)
        
        auth = aiohttp.BasicAuth(hub_login["u"], hub_login["p"])
        url = "https://mob.yalehomesystem.co.uk/yapi/o/token/"
        data = {"grant_type": "password", "username": self._username, "password": self._password}
        headers = {"Accept": "application/json"}
        result = await self.api_wrapper("post",url,data,headers,auth)
        try:
            self._access_token = result["access_token"]
            self._refresh_token = result["refresh_token"]
            self._token_expires = datetime.now() + timedelta(seconds=result["expires_in"])
            return True
        except Exception as exception:
            _LOGGER.info(exception)
            return False
    
    async def async_status(self) -> dict:
        try:
            await self.async_login()
            url = "https://mob.yalehomesystem.co.uk/yapi/api/panel/cycle/"
            headers = {"Authorization": f"Bearer {self._access_token}"}
            data = {}
            result = await self.api_wrapper("get",url,data,headers)
            return result
        except Exception as exception:
            _LOGGER.info(exception)
    
    async def async_lock(self, device_id: str, area: int = 1, zone: int = 1) -> bool:
        try:        
            await self.async_login()
            
            data = aiohttp.FormData()
            data.add_field("area",area)
            data.add_field("zone",zone)
            data.add_field("device_sid",device_id)
            data.add_field("device_type","device_type.door_lock")
            data.add_field("request_value",1)
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            url = "https://mob.yalehomesystem.co.uk/yapi/api/panel/device_control/"
            
            result = await self.api_wrapper("post", url, data, headers)
            if result["code"] == "000":
                return True
        except Exception as exception:
            _LOGGER.info(exception)
        return False
    
    async def async_unlock(self, device_id: str, area: int = 1, zone: int = 1, pincode: str = "") -> bool:
        try:
            await self.async_login()
            
            data = aiohttp.FormData()
            data.add_field("area",area)
            data.add_field("zone",zone)
            data.add_field("pincode",pincode)
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            url = "https://mob.yalehomesystem.co.uk/yapi/api/minigw/unlock/"
            
            result = await self.api_wrapper("post", url, data, headers)
            if result["code"] == "000":
                return True
        except Exception as exception:
            _LOGGER.info(exception)
        return False
    
    async def api_wrapper(self, method: str, url: str, data: dict = {}, headers: dict = {}, auth = None) -> dict:
        try:
            async with async_timeout.timeout(TIMEOUT):
                if method == "get":
                    response = await self._session.get(url, headers=headers, auth=auth)
                    result = await response.json()
                    return result
                elif method == "put":
                    await self._session.put(url, headers=headers, json=data, auth=auth)
                elif method == "patch":
                    await self._session.patch(url, headers=headers, json=data, auth=auth)
                elif method == "post":
                    response = await self._session.post(url, headers=headers, data=data, auth=auth)
                    result = await response.json()
                    return result
            
        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )
            
        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:
            _LOGGER.error("Something really wrong happened! - %s", exception)

    async def async_get_yale_event_log(self, page_number: str = "1") -> dict:
        """
        Download the last month's event log from Yale API.
        """
        try:
            url = f"https://mob.yalehomesystem.co.uk/yapi/api/event/report/?page_num={page_number}&set_utc=0"
            data = {}
            headers = {
                    "Authorization": f"Bearer {self._access_token}"
            }
            _LOGGER.info("Downloaded page %s from Yale event log. url: %s", page_number, url)
            return await self.api_wrapper("get", url, data, headers)

        except Exception as exception:
            _LOGGER.error("Failed to fetch Yale event log (page %s): %s", page_number, exception)
