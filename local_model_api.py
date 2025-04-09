import aiohttp
import logging

logger = logging.getLogger("main")

class LocalModelAPI:
    """
    API client for local ML model using async requests.
    """

    def __init__(self, url="http://localhost:8000"):
        """
        Initialize the API client.

        Args:
            url (str): URL of the local ML model API (default: "http://localhost:8000").
        """
        self.url = url

    async def predict(self, data):
        """
        Make a prediction using the local ML model.

        Args:
            data (dict): Input data for prediction.

        Returns:
            dict: Prediction result.

        Raises:
            Exception: If the request fails.
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.url}/predict", json=data) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get prediction: {response.status}")
                    return await response.json()
            except Exception as e:
                logger.error(f"Failed to make prediction: {type(e).__name__}: {str(e)}")
                raise
