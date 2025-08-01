import threading
from threading import Lock
import time

from tasks.Task import Task
from bot_related.bot_config import BotConfig
from bot_related.device_gui_detector import GuiDetector, GuiName

from filepath.file_relative_paths import ImagePathAndProps, VERIFICATION_CLOSE_REFRESH_OK, VERIFICATION_VERIFY_TITLE
from tasks.Alliance import Alliance
from tasks.Barbarians import Barbarians
from tasks.Break import Break
from tasks.ClaimQuests import ClaimQuests
from tasks.ClaimVip import ClaimVip
from tasks.Collecting import Collecting
from tasks.GatherResource import GatherResource
from tasks.LocateBuildings import LocateBuilding
from tasks.Materials import Materials
from tasks.Restart import Restart
from tasks.Scout import Scout
from tasks.ScreenShot import ScreenShot
from tasks.Tavern import Tavern
from tasks.Training import Training
from tasks.MysteryMerchant import MysteryMerchant
from tasks.GatherGem import GatherGem
from tasks.constants import TaskName
from utils import stop_thread, set_gui_log_handler, gui_log, check_bot_health, safe_operation, MarchManager
import random
import time

DEFAULT_RESOLUTION = {'height': 720, 'width': 1280}


class Bot():

    def __init__(self, device, config={}, gui_handler=None):
        self.daemon_thread = None
        self.curr_thread = None
        self.device = device
        self.gui = GuiDetector(device)
        self.text_update_event = lambda v: v
        self.text = {
            'title': '',
            'text_list': []
        }

        self.building_pos_update_event = lambda **kw: kw
        self.config_update_event = lambda **kw: kw
        
        # Connect to GUI logging if handler provided
        if gui_handler is not None:
            set_gui_log_handler(gui_handler)
            gui_log("Bot inicializado", "INFO")

        # get screen resolution
        str = device.shell('wm size').replace('\n', '')
        height, width = list(map(int, str[(str.find(':') + 1):len(str)].split('x')))
        self.resolution = {
            'height': height,
            'width': width
        }

        self.building_pos = {}

        self.config = BotConfig(config)
        self.curr_task = TaskName.BREAK

        self.task = Task(self)
        
        # Initialize March Manager
        self.march_manager = MarchManager(self)

        # tasks
        self.restart_task = Restart(self)
        self.break_task = Break(self)
        self.mystery_merchant_task = MysteryMerchant(self)
        self.alliance_task = Alliance(self)
        self.barbarians_task = Barbarians(self)
        self.claim_quests_task = ClaimQuests(self)
        self.claim_vip_task = ClaimVip(self)
        self.collecting_task = Collecting(self)
        self.gather_resource_task = GatherResource(self)
        self.gather_gem_task = GatherGem(self)
        self.locate_building_task = LocateBuilding(self)
        self.materials_task = Materials(self)
        self.scout_task = Scout(self)
        self.tavern_task = Tavern(self)
        self.training = Training(self)

        # Other task
        self.screen_shot_task = ScreenShot(self)

        self.round_count = 0

    def start(self, fn):
        gui_log("Iniciando bot...", "INFO")
        
        if self.daemon_thread is not None and self.daemon_thread.is_alive():
            gui_log("Deteniendo thread daemon anterior", "WARNING")
            stop_thread(self.daemon_thread)
            print('daemon_thread: {}', self.daemon_thread.is_alive())

        if self.curr_thread is not None and self.curr_thread.is_alive():
            gui_log("Deteniendo thread principal anterior", "WARNING")
            stop_thread(self.curr_thread)
            print('curr_thread: {}', self.curr_thread.is_alive())
        
        gui_log("Bot iniciado correctamente", "SUCCESS")
        self.daemon(fn)

    def stop(self):
        gui_log("Deteniendo bot...", "INFO")
        
        if self.daemon_thread is not None and self.daemon_thread.is_alive():
            gui_log("Deteniendo thread daemon", "WARNING")
            stop_thread(self.daemon_thread)
            print('daemon_thread: {}', self.daemon_thread.is_alive())

        if self.curr_thread is not None and self.curr_thread.is_alive():
            gui_log("Deteniendo thread principal", "WARNING")
            stop_thread(self.curr_thread)
            print('curr_thread: {}', self.curr_thread.is_alive())
        
        gui_log("Bot detenido", "INFO")


    def get_city_image(self):
        return self.screen_shot_task.do_city_screen()

    def do_task(self, curr_task=TaskName.COLLECTING):
        gui_log(f"Iniciando ciclo de tareas - Tarea actual: {curr_task}", "INFO")

        tasks = [
            [self.mystery_merchant_task, 'enableMysteryMerchant'],
            [self.alliance_task, 'allianceAction', 'allianceDoRound'],
            [self.barbarians_task, 'attackBarbarians'],
            [self.claim_quests_task, 'claimQuests', 'questDoRound'],
            [self.claim_vip_task, 'enableVipClaimChest', 'vipDoRound'],
            [self.collecting_task, 'enableCollecting'],
            [self.gather_resource_task, 'gatherResource'],
            [self.gather_gem_task, 'enableGatherGem'],
            [self.materials_task, 'enableMaterialProduce' , 'materialDoRound'],
            [self.scout_task, 'enableScout'],
            [self.tavern_task, 'enableTavern'],
            [self.training, 'enableTraining'],
        ]

        if self.building_pos is None:
            curr_task = TaskName.INIT_BUILDING_POS

        while True:
            random.shuffle(tasks)
            # restart
            if curr_task == TaskName.KILL_GAME and self.config.enableStop \
                    and self.round_count % self.config.stopDoRound == 0:
                curr_task = self.restart_task.do(TaskName.BREAK)
            elif curr_task == TaskName.KILL_GAME:
                curr_task = TaskName.BREAK

            # init building position if need
            if not self.config.hasBuildingPos or curr_task == TaskName.INIT_BUILDING_POS:
                curr_task = self.locate_building_task.do(next_task=TaskName.COLLECTING)
            elif curr_task == TaskName.BREAK and self.config.enableBreak \
                    and self.round_count % self.config.breakDoRound == 0:
                curr_task = self.break_task.do(TaskName.COLLECTING)
            elif curr_task == TaskName.BREAK:
                curr_task = self.break_task.do_no_wait(TaskName.KILL_GAME)

            for task in tasks:
                task_name = task[0].__class__.__name__
                if len(task) == 2:
                    if getattr(self.config, task[1]):
                        gui_log(f"Ejecutando tarea: {task_name}", "INFO")
                        curr_task = task[0].do()
                else:
                    if getattr(self.config, task[1]) and self.round_count % getattr(self.config, task[2]) == 0:
                        gui_log(f"Ejecutando tarea: {task_name}", "INFO")
                        curr_task = task[0].do()

            if self.config.enableStop:
                curr_task = TaskName.KILL_GAME
            else:
                curr_task = TaskName.BREAK

            self.round_count = self.round_count + 1
            gui_log(f"Ciclo completado - Ronda #{self.round_count}", "INFO")
            
                    # Check bot health every 5 rounds
        if self.round_count % 5 == 0:
            check_bot_health()
            # Log march status
            self.march_manager.log_march_status()
                
            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)
        return

    def daemon(self, fn):
        def run():
            gui_log("Iniciando thread daemon", "INFO")
            main_thread = threading.Thread(target=fn)
            self.curr_thread = main_thread
            main_thread.start()

            while True:
                if self.daemon_thread is None or not main_thread.is_alive():
                    gui_log("Thread daemon terminando", "INFO")
                    break
                
                # Check every 30 seconds instead of 60 for faster response
                time.sleep(30)
                
                # Check if main thread is stuck
                if main_thread.is_alive():
                    gui_log("Verificando estado del thread principal", "INFO")
                    
                    # Check for verification dialogs
                    try:
                        found, _, pos = self.gui.check_any(ImagePathAndProps.VERIFICATION_VERIFY_TITLE_IMAGE_PATH.value)
                        if found:
                            gui_log("Dialogo de verificación detectado", "WARNING")
                            found, _, pos = self.gui.check_any(ImagePathAndProps.VERIFICATION_CLOSE_REFRESH_OK_BUTTON_IMAGE_PATH.value)
                            if not found:
                                gui_log("Cerrando dialogo de verificación", "INFO")
                                stop_thread(main_thread)
                                time.sleep(1)
                                main_thread = threading.Thread(target=fn)
                                self.curr_thread = main_thread
                                main_thread.start()
                    except Exception as e:
                        gui_log(f"Error verificando dialogo: {e}", "ERROR")
                else:
                    gui_log("Thread principal terminado, reiniciando", "WARNING")
                    main_thread = threading.Thread(target=fn)
                    self.curr_thread = main_thread
                    main_thread.start()

        daemon_thread = threading.Thread(target=run)
        daemon_thread.start()
        self.daemon_thread = daemon_thread


