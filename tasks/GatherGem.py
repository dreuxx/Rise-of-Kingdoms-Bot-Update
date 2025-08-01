import traceback
import logging

from filepath.constants import MAP
from filepath.file_relative_paths import (
    BuffsImageAndProps,
    ItemsImageAndProps,
    ImagePathAndProps,
)
from tasks.Task import Task
from tasks.constants import TaskName, Resource
import time

# Configure logging
logger = logging.getLogger(__name__)


class GatherGem(Task):
    def __init__(self, bot):
        super().__init__(bot)
        self.move_time = {"up": 0, "down": 0, "left": 0, "right": 0}
        self.last_move = "up"
        self.debug_mode = False  # Set to True for debugging

    def reset_move(self):
        """Reset move counters"""
        self.move_time["up"] = 0
        self.move_time["down"] = 0
        self.move_time["left"] = 0
        self.move_time["right"] = 0

    def get_next_move(self, allowed_time=50):
        """Function to decide what to move next, however it may missed some direction"""
        next_move = "done"
        if self.move_time["up"] >= allowed_time:
            if self.move_time["down"] >= allowed_time:
                if self.move_time["left"] >= allowed_time:
                    if self.move_time["right"] >= allowed_time:
                        self.reset_move()
                        return next_move
                    else:
                        next_move = "right"
                else:
                    next_move = "left"
            else:
                next_move = "down"
        else:
            next_move = "up"
        self.move_time[next_move] = self.move_time[next_move] + 1
        return next_move

    def do_move(self):
        """Execute movement on the map"""
        next_move = self.get_next_move(self.bot.config.gatherGemDistance)
        if next_move == "done":
            self.last_move = "up"
            return False
        if next_move != self.last_move:
            self.back_to_home_gui()
            self.back_to_map_gui()
            self.last_move = next_move
        self.move(next_move)
        return True

    def do(self, next_task=TaskName.GATHER_GEM):
        """Main gem gathering task"""
        magnifier_pos = (60, 540)
        self.set_text(title="Gather Gem", remove=True)

        # Debug mode control
        if self.debug_mode:
            logger.info("Debug: GatherGem task starting")
            logger.info(f"Debug: Magnifier position: {magnifier_pos}")

        # Start at any map location
        self.back_to_map_gui()
        last_resource_pos = []
        last_dir = "up"
        
        # List of all gem image paths for multiple detection
        gem_image_paths = [
            ImagePathAndProps.GEM_IMG_PATH.value,
            ImagePathAndProps.GEM_IMG_PATH_1.value,
            ImagePathAndProps.GEM_IMG_PATH_2.value,
            ImagePathAndProps.GEM_IMG_PATH_3.value,
            ImagePathAndProps.GEM_IMG_PATH_4.value,
            ImagePathAndProps.GEM_IMG_PATH_5.value,
            ImagePathAndProps.GEM_IMG_PATH_6.value,
            ImagePathAndProps.GEM_IMG_PATH_7.value,
            ImagePathAndProps.GEM_IMG_PATH_8.value,
            ImagePathAndProps.GEM_IMG_PATH_9.value,
            ImagePathAndProps.GEM_IMG_PATH_10.value,
            ImagePathAndProps.GEM_IMG_PATH_11.value,
            ImagePathAndProps.GEM_IMG_PATH_12.value,
            ImagePathAndProps.GEM_IMG_PATH_13.value,
            ImagePathAndProps.GEM_IMG_PATH_14.value,
            ImagePathAndProps.GEM_IMG_PATH_15.value,
        ]
        
        # Use multiple images only if configured
        if not self.bot.config.gatherGemUseMultipleImages:
            gem_image_paths = [ImagePathAndProps.GEM_IMG_PATH.value]
        
        try:
            while True:
                # Check if gem mine exists on map using multiple images
                found = False
                gempost = None
                found_images = []
                
                for i, gem_path in enumerate(gem_image_paths):
                    if self.debug_mode:
                        found_single, _, pos = self.debug_check_any(gem_path)
                        if not found_single and i == 0:  # Only save debug image for first attempt
                            self.save_debug_image("gem_not_found")
                    else:
                        found_single, _, pos = self.gui.check_any(gem_path)
                    
                    if found_single:
                        found_images.append((i+1, pos))
                        if self.debug_mode:
                            logger.info(f"Debug: Gem found with image {i+1}")
                
                # Determine if we have enough confirmations
                if len(found_images) >= self.bot.config.gatherGemMinImagesFound:
                    found = True
                    # Use the first found position
                    gempost = found_images[0][1]
                    if self.debug_mode:
                        logger.info(f"Debug: Confirmed gem with {len(found_images)} images")
                elif len(found_images) > 0:
                    # If we found some but not enough, still use it but log
                    found = True
                    gempost = found_images[0][1]
                    if self.debug_mode:
                        logger.info(f"Debug: Partial confirmation with {len(found_images)} images")

                if found:
                    self.set_text(insert="Found gem mine")
                    # Tap on the gem mine
                    self.tap(gempost[0], gempost[1], 2)
                    new_resource_pos = (
                        self.gui.resource_location_image_to_string()
                    )
                    if new_resource_pos in last_resource_pos:
                        self.set_text(insert="Same node of gem")
                        # Same node, move the screen
                        if not self.do_move():
                            return next_task
                        continue
                    else:
                        # Save last node position, remember to reset the last resource pos
                        last_resource_pos.append(new_resource_pos)
                    
                    # Check if we can gather the node
                    if self.debug_mode:
                        found, _, gather_button_pos = self.debug_check_any(
                            ImagePathAndProps.RESOURCE_GATHER_BUTTON_IMAGE_PATH.value
                        )
                        if not found:
                            self.save_debug_image("gem_gather_button_not_found")
                    else:
                        found, _, gather_button_pos = self.gui.check_any(
                            ImagePathAndProps.RESOURCE_GATHER_BUTTON_IMAGE_PATH.value
                        )

                    if found:
                        # Yes, send the troop
                        self.tap(gather_button_pos[0], gather_button_pos[1], 2)

                        if self.debug_mode:
                            result = self.debug_check_any(
                                ImagePathAndProps.NEW_TROOPS_BUTTON_IMAGE_PATH.value
                            )
                            if not result[0]:
                                self.save_debug_image(
                                    "gem_new_troops_button_not_found"
                                )
                            pos = result[2]
                        else:
                            pos = self.gui.check_any(
                                ImagePathAndProps.NEW_TROOPS_BUTTON_IMAGE_PATH.value
                            )[2]

                        if pos is None:
                            self.set_text(insert="No more space for march")
                            if self.bot.config.useAllMarches and self.bot.config.waitForMarches:
                                self.set_text(insert="Esperando espacio de marcha para gemas...")
                                if not self.bot.march_manager.wait_for_march_space(
                                    timeout=self.bot.config.maxWaitTime, 
                                    task_name="Gather Gem"
                                ):
                                    self.set_text(insert="Timeout esperando marcha para gemas")
                                    if self.bot.config.autoSwitchTasks:
                                        next_task = self.bot.march_manager.switch_to_available_task() or next_task
                                    return next_task
                                # Try again after waiting
                                pos = self.gui.check_any(
                                    ImagePathAndProps.NEW_TROOPS_BUTTON_IMAGE_PATH.value
                                )[2]
                                if pos is None:
                                    self.set_text(insert="Aún no hay espacio de marcha")
                                    return next_task
                            else:
                                return next_task
                        new_troops_button_pos = pos
                        self.tap(
                            new_troops_button_pos[0],
                            new_troops_button_pos[1],
                            2,
                        )
                        if (
                            True
                        ):  # self.bot.config.gatherResourceNoSecondaryCommander:
                            self.set_text(insert="Remove secondary commander")
                            self.tap(473, 462, 0.5)
                        # Send match
                        if self.debug_mode:
                            result = self.debug_check_any(
                                ImagePathAndProps.TROOPS_MATCH_BUTTON_IMAGE_PATH.value
                            )
                            if not result[0]:
                                self.save_debug_image(
                                    "gem_troops_match_button_not_found"
                                )
                            match_button_pos = result[2]
                        else:
                            match_button_pos = self.gui.check_any(
                                ImagePathAndProps.TROOPS_MATCH_BUTTON_IMAGE_PATH.value
                            )[2]

                        self.set_text(insert="March")
                        self.tap(match_button_pos[0], match_button_pos[1], 2)
                    else:
                        # Can't gather it, maybe farmed by anyone else
                        self.set_text(insert="Not farmable")
                        # Try to move screen
                        if not self.do_move():
                            return next_task
                        continue
                else:
                    if not self.do_move():
                        return next_task
        except Exception as e:
            logger.error(f"Error in GatherGem task: {e}")
            traceback.print_exc()
            return next_task
        return next_task

    def check_query_space(self):
        """Check available march slots"""
        if self.debug_mode:
            found, _, _ = self.debug_check_any(
                ImagePathAndProps.HAS_MATCH_QUERY_IMAGE_PATH.value
            )
            if not found:
                self.save_debug_image("gem_match_query_not_found")
        else:
            found, _, _ = self.gui.check_any(
                ImagePathAndProps.HAS_MATCH_QUERY_IMAGE_PATH.value
            )

        curr_q, max_q = self.gui.match_query_to_string()
        if curr_q is None:
            return self.max_query_space
        return max_q - curr_q