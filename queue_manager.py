import aio_pika
import logging

logger = logging.getLogger("main")

class QueueManager:
    """
    Manage task queues using RabbitMQ with error handling.
    """

    def __init__(self, url="amqp://guest:guest@localhost/"):
        """
        Initialize the queue manager.

        Args:
            url (str): RabbitMQ URL (default: "amqp://guest:guest@localhost/").
        """
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        """
        Connect to RabbitMQ with retry logic.

        Raises:
            Exception: If connection fails after retries.
        """
        retries = 3
        for attempt in range(retries):
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                await self.channel.declare_queue("trading_tasks")
                logger.info("Successfully connected to RabbitMQ")
                return
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt+1}/{retries}): {type(e).__name__}: {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                else:
                    raise Exception("Failed to connect to RabbitMQ after retries")

    async def publish_task(self, task):
        """
        Publish a task to the queue.

        Args:
            task (str): Task to publish.

        Raises:
            Exception: If publishing fails.
        """
        if not self.channel:
            await self.connect()
        try:
            await self.channel.default_exchange.publish(
                aio_pika.Message(body=task.encode()),
                routing_key="trading_tasks"
            )
            logger.debug(f"Published task to RabbitMQ: {task}")
        except Exception as e:
            logger.error(f"Failed to publish task to RabbitMQ: {type(e).__name__}: {str(e)}")
            raise

    async def close(self):
        """
        Close the RabbitMQ connection.
        """
        if self.connection:
            try:
                await self.connection.close()
                logger.info("Closed RabbitMQ connection")
            except Exception as e:
                logger.error(f"Failed to close RabbitMQ connection: {type(e).__name__}: {str(e)}")
