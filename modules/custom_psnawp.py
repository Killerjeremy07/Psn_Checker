# Custom wrapper made on top of PSNAWP which presents some outdated features
import json
from typing import Any

from psnawp_api.core.psnawp_exceptions import PSNAWPNotFound
from psnawp_api.utils.endpoints import BASE_PATH
from psnawp_api.utils.request_builder import RequestBuilder

class Search:
    def __init__(self, request_builder: RequestBuilder):
        """The Search class provides the information and methods for searching resources on playstation network.

        :param request_builder: The instance of RequestBuilder. Used to make HTTPRequests.
        :type request_builder: RequestBuilder

        """
        self._request_builder = request_builder

    def universal_search(self, search_query: str, search_context: str) -> dict[str, Any]:
        """Searches the PlayStation Website using the new GraphQL endpoint."""

        url = "https://m.np.playstation.com/api/graphql/v1/op"
        variables = {
            "searchTerm": search_query,
            "searchContext": search_context
        }

        extensions = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "a2fbc15433b37ca7bfcd7112f741735e13268f5e9ebd5ffce51b85acc126f41d"
            }
        }

        payload = {
            "operationName": "metGetContextSearchResults",
            "variables": variables,
            "extensions": extensions
        }

        response: dict[str, Any] = self._request_builder.post(url=url, data=json.dumps(payload)).json()
        filtered_response = response["data"]["universalContextSearch"]["results"][0]["searchResults"]

        return filtered_response
