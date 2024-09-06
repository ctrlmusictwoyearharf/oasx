# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import datetime, timedelta, time  # type: ignore

# sys.path.append('D:\\project\\OnmyojiAutoScript')

from tasks.Component.BaseActivity.base_activity import BaseActivity
from tasks.Component.BaseActivity.config_activity import ApMode
from tasks.HeroTest.assets import HeroTestAssets
from tasks.GameUi.page import page_main
from tasks.GameUi.game_ui import GameUi

from module.logger import logger
from module.exception import TaskEnd


class ScriptTask(GameUi, BaseActivity, HeroTestAssets):

    def run(self) -> None:

        config = self.config.HeroTest
        self.limit_time: timedelta = config.general_climb.limit_time
        if isinstance(self.limit_time, time):
            self.limit_time = timedelta(
                hours=self.limit_time.hour,
                minutes=self.limit_time.minute,
                seconds=self.limit_time.second,
            )
        self.limit_count = config.general_climb.limit_count

        self.ui_get_current_page()
        self.ui_goto(page_main)
        self.home_main()

        # # 2024-04-04 ---------------------start
        # config.general_climb.ap_mode = ApMode.AP_GAME
        # # 2024-04-04 ---------------------end
        # 选择是游戏的体力还是活动的体力
        current_ap = config.general_climb.ap_mode
        # self.switch(current_ap)

        # 设定是否锁定阵容
        if config.general_battle.lock_team_enable:
            logger.info("Lock team")
            while 1:
                self.screenshot()
                if self.appear_then_click(self.I_UNLOCK, interval=1):
                    continue
                if self.appear(self.I_LOCK):
                    break
        else:
            logger.info("Unlock team")
            while 1:
                self.screenshot()
                if self.appear_then_click(self.I_LOCK, interval=1):
                    continue
                if self.appear(self.I_UNLOCK):
                    break

        # 流程应该是 在页面处：
        # 1. 判定计数是否超了，时间是否超了
        # 2. 如果是消耗活动体力，判定活动体力是否足够 如果是消耗一般的体力，判定一般体力是否足够
        # 3. 如果开启买体力，就买体力
        # 4. 如果开启了切换到游戏体力，就切换
        while 1:
            # 1
            if (
                self.limit_time is not None
                and self.limit_time + self.start_time < datetime.now()
            ):
                logger.info("Time out")
                break
            if self.current_count >= self.limit_count:
                logger.info("Count out")
                break
            # 2
            self.wait_until_appear(self.I_BATTLE)
            # is_remain = self.check_ap_remain(current_ap)
            is_remain = True
            # 如果没有剩余了且这个时候是体力，就退出活动
            if not is_remain and current_ap == ApMode.AP_GAME:
                logger.info("Game ap out")
                break

            # 点击战斗
            logger.info("Click battle")
            while 1:
                self.screenshot()
                if self.appear_then_click(self.I_BATTLE, interval=2):
                    self.device.stuck_record_clear()
                    continue
                if not self.appear(self.I_BATTLE):
                    break

                if self.appear_then_click(self.I_UI_CONFIRM_SAMLL, interval=1):
                    continue
                if self.appear_then_click(self.I_UI_CONFIRM, interval=1):
                    continue

            if self.run_general_battle(config=config.general_battle):
                logger.info("General battle success")

        self.main_home()
        self.set_next_run(task="ActivityShikigami", success=True)
        raise TaskEnd

    def home_main(self) -> bool:
        """
        从庭院到活动的爬塔界面
        :return:
        """
        # 启动经验加成
        self.open_buff()
        self.exp_100(True)
        self.exp_50(True)
        self.close_buff()
        logger.hr("Enter Shikigami", 2)
        while 1:
            self.screenshot()
            if self.appear(self.I_BATTLE):
                logger.info("发现了战斗按钮，进入活动界面成功")
                break
            # 2024-04-04 --------------start
            if self.appear_then_click(self.I_ONE, interval=1):
                continue
            # 2024-04-04 --------------end
            if self.appear_then_click(self.I_TWO, interval=1):
                continue
            if self.appear_then_click(self.I_GBB, interval=1):
                continue

    def main_home(self) -> bool:
        """
        从活动的爬塔界面到庭院
        :return:
        """
        logger.hr("Exit Shikigami", 2)
        while 1:
            self.screenshot()
            if self.appear(self.I_ONE):
                # 关闭经验加成
                self.open_buff()
                self.exp_100(False)
                self.exp_50(False)
                self.close_buff()
                break
            if self.appear_then_click(self.I_UI_BACK_RED, interval=2):
                continue
            if self.appear_then_click(self.I_UI_BACK_YELLOW, interval=2):
                continue
            if self.appear_then_click(self.I_BACK, interval=2):
                continue
            if self.appear_then_click(self.I_GBB_BACK, interval=2):
                continue

    def check_ap_remain(self, current_ap: ApMode) -> bool:
        """
        检查体力是否足够
        :return: 如何还有体力，返回True，否则返回False
        """
        self.screenshot()
        # 用不到活动体力
        if current_ap == ApMode.AP_ACTIVITY:
            cu, res, total = self.O_REMAIN_AP_ACTIVITY.ocr(image=self.device.image)
            if cu == 0 and cu + res == total:
                logger.warning("Activity ap not enough")
                return False
            return True
        elif current_ap == ApMode.AP_GAME:
            cu, res, total = self.O_REMAIN_AP.ocr(image=self.device.image)
            if cu == total and cu + res == total:
                if cu > total:
                    logger.warning(f"Game ap {cu} more than total {total}")
                    return True
                logger.warning(f"Game ap not enough: {cu}")
                return False
            return True


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    c = Config("oas1")
    d = Device(c)
    t = ScriptTask(c, d)

    t.run()
