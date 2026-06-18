from actions import UserAction
from auth import Authenticator
from user_interface import UserInterface
from workflow_factory import WorkflowFactory


class App:
    """Собирает зависимости и запускает сценарии приложения."""

    def __init__(
        self,
        user: dict,
        ui: UserInterface,
        workflow_factory: WorkflowFactory,
    ) -> None:
        self.user = user
        self.ui = ui
        self.workflow_factory = workflow_factory

    @classmethod
    def create(cls) -> "App":
        """Создать приложение с авторизованным Spotify-клиентом."""
        authenticator = Authenticator()
        spotify = authenticator.create_client()
        user = spotify.current_user()
        ui = UserInterface()
        workflow_factory = WorkflowFactory(
            spotify,
            user,
            ui,
        )

        return cls(user, ui, workflow_factory)

    def run(self) -> None:
        """Запустить приложение."""
        self.ui.show_authorized_user(self.user)
        workflow = self.workflow_factory.create(UserAction.TRANSFER_LIKED_TRACKS)
        workflow.run()
