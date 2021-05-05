from log_gen import LogGen
from web_service import WebService
import subprocess

web_service = WebService()
logger = LogGen().loggen()


class UpgradeDistri:

    def __init__(self):
        logger.info('upgrade distri')
        web_service.set_distri_upgrade(1)

        bash_command = "apt-get -y update && apt-get -y dist-upgrade"
        try:
            subprocess.run(['bash', '-c', bash_command], check=True)
            status = 2
        except subprocess.CalledProcessError as e:
            logger.error(e)
            status = 3

        web_service.set_distri_upgrade(status)
        logger.info('upgrade distri terminé avec succès')


if __name__ == "__main__":
    upgrade = UpgradeDistri()
