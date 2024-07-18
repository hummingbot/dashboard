from frontend.components.deploy_v2_with_controllers import LaunchV2WithControllers
from frontend.st_utils import initialize_st_page

initialize_st_page(title="Launch Bot ST", icon="🙌")


launcher = LaunchV2WithControllers()
launcher()
