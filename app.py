import logging
from typing import Self

from actions import UserAction
from api.types import SpotifyUser
from auth import Authenticator
from ui import UserInterface
from workflow_factory import WorkflowFactory

logger = logging.getLogger(__name__)


class App:
    """Собирает зависимости и запускает сценарии приложения."""

    def __init__(
        self,
        user: SpotifyUser,
        ui: UserInterface,
        workflow_factory: WorkflowFactory,
    ) -> None:
        self.user = user
        self.ui = ui
        self.workflow_factory = workflow_factory

    @classmethod
    def create(cls: type[Self]) -> Self:
        """Создать приложение с авторизованным Spotify-клиентом."""
        logger.info("App creation started")
        authenticator = Authenticator()
        spotify = authenticator.create_client()
        logger.info("Spotify client created")
        user = spotify.current_user()
        logger.info("Current Spotify user loaded")
        ui = UserInterface()
        workflow_factory = WorkflowFactory(
            spotify,
            user,
            ui,
        )

        return cls(user, ui, workflow_factory)

    def run(self) -> None:
        """Запустить приложение."""
        logger.info("App started")
        self.ui.show_authorized_user(self.user)
        logger.info(
            "Workflow selected: action=%s",
            UserAction.TRANSFER_LIKED_TRACKS.value,
        )
        workflow = self.workflow_factory.create(UserAction.TRANSFER_LIKED_TRACKS)
        workflow.run()
