import aio_pika

class QueueManager:
    """
    Manage task queues using RabbitMQ.
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
        Connect to RabbitMQ.
        """
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue("trading_tasks")

    async def publish_task(self, task):
        """
        Publish a task to the queue.

        Args:
            task (str): Task to publish.
        """
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=task.encode()),
            routing_key="trading_tasks"
        )

    async def close(self):
        """
        Close the RabbitMQ connection.
        """
        await self.connection.close()
