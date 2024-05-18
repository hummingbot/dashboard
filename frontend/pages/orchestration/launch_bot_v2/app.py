from frontend.components.deploy_v2_with_controllers import LaunchV2WithControllers
from frontend.st_utils import initialize_st_page

CARD_WIDTH = 6
CARD_HEIGHT = 3
NUM_CARD_COLS = 2

initialize_st_page(title="Launch Bot", icon="🙌")


launcher = LaunchV2WithControllers()
launcher()
