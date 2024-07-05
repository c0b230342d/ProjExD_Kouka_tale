import os
import sys
import pygame as pg
from pygame.locals import *
import pygame.mixer
import time
import random
import math

"""
以下、複数個のクラス等で参照回数が多いかつ、値の変化がないものを
グローバル変数とする
"""
# グローバル変数
WIDTH, HEIGHT = 1024, 768 # ディスプレイサイズ
FONT = "font/JF-Dot-MPlusS10.ttf"  # ドット文字細目
FONT_F = "font/JF-Dot-MPlusS10B.ttf"  # ドット文字太目
GRAVITY = 0.75  #重力の大きさ。ジャンプした時に落ちる力。

os.chdir(os.path.dirname(os.path.abspath(__file__)))

"""
画面のあたり判定に関する関数
"""
def check_bound1(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

def check_bound2(obj_rct:pg.Rect) -> tuple[bool, bool]:
    """
    引数:ハートRect
    戻り値:タプル(横方向判定結果, 縦方向判定結果)
    行動範囲内ならTrue, 行動範囲外ならFalseを返す
    """
    yoko, tate = True, True
    if obj_rct.left < WIDTH/2-150+5 or WIDTH/2+150-5 < obj_rct.right:  # 横判定
        yoko = False
    if obj_rct.top < HEIGHT/2-50+5 or (HEIGHT/2-50)+300-5 < obj_rct.bottom:  # 縦判定
        tate = False
    return yoko, tate

def check_bound(obj_rct:pg.Rect, left:int, right:int, top:int, bottom:int) -> tuple[bool, bool]:
    """
    与えられた引数より外側にあるか否かを判断しそれに応じたTrue or Falseを返す
    引数1 obj_rct:判定したいオブジェクトのrect
    引数2 left:左側の座標
    引数3 right:右側の座標
    引数4 top:上の座標
    引数5 bottom:下の座標
    """
    yoko, tate = True, True
    if obj_rct.left < left or right < obj_rct.right:
        yoko = False
    if obj_rct.top < top or bottom < obj_rct.bottom:
        tate = False
    return yoko, tate

"""
プレイヤーを追従する際に使う関数(講義資料のまま)
"""
def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

"""
以下のクラスは変更しなくてよい（初期設定）
開発する時はすべて折りたたんでおいた方がわかりやすいかも
"""
class Koukaton(pg.sprite.Sprite):
    """
    こうかとん表示に関するクラス
    """
    img = pg.transform.rotozoom(
        pg.image.load("fig/dot_kk_negate.png"),
        0,1.5
    )
    def __init__(self):
        """
        こうかとん画像Surfaceを生成する
        """
        super().__init__()
        self.image = __class__.img
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = WIDTH/2, HEIGHT/4+30

    def update(self, screen: pg.Surface):
        """
        こうかとんを表示
        """
        screen.blit(self.image, self.rect)

    
class Heart(pg.sprite.Sprite):
    """
    プレイヤー（ハート）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img = pg.transform.rotozoom(
        pg.image.load("fig/Undertale_hurt.png"), 
        0, 0.02
        ) 
    invincible_time = 30  # 無敵時間
    
    def __init__(self, xy: tuple[int, int]):
        """
        ハート画像Surfaceを生成する
        引数 xy：ハート画像の初期位置座標タプル
        """
        super().__init__()
        self.image = __class__.img
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = xy
        self.invincible = False

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてハートを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(sum_mv)
        if check_bound2(self.rect) != (True, True):
            self.rect.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.image = __class__.img
        if sum_mv != [0, 0]:
            self.dire = sum_mv
        if self.invincible:  # 無敵時間の設定
            if self.invincible_time == 0:
                self.invincible = False
                self.invincible_time = __class__.invincible_time
            else:
                self.invincible_time -= 1
                if self.invincible_time % 5 == 0:
                    screen.blit(self.image, self.rect)
        else:        
            screen.blit(self.image, self.rect)
            
        
class HeartGrav(pg.sprite.Sprite):
    """
    プレイヤー（ハート）に関するクラス
    """
    img = pg.transform.rotozoom(
        pg.image.load("fig/Undertale_hurt.png"), 
        0, 0.02
        )

    dx = 0  # x軸方向の移動量
    dy = 0  # y軸方向の移動量

    invincible_time = 30  # 無敵時間
    
    def __init__(self, xy: tuple[int, int]):
        """
        ハート画像Surfaceを生成する
        引数 xy：ハート画像の初期位置座標タプル
        """
        super().__init__()
        self.image = __class__.img
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = xy

		# heartの移動スピードを代入
        self.speed = +5.0
		# Y軸方向の速度
        self.vel_y = 0
		# 空中にいるかどうかのフラグ
        self.in_air = True

        self.invincible = False

    def update(self, key_lst, screen: pg.Surface):
        """
        押下キーに応じてハートを移動させる
		引数1 moving_left：左移動フラグ
		引数2 moving_right：右移動フラグ
        引数3 screen：画面Surface
		"""
		# 移動量をリセット。dx,dyと表記しているのは微小な移動量を表すため。微分、積分で使うdx,dy。
        dx = 0
        dy = 0

		# 左に移動
        if key_lst[pg.K_LEFT]:
			# スピードの分だけ移動。座標系において左は負の方向
            dx = -self.speed

		# 右に移動
        if key_lst[pg.K_RIGHT]:
			# スピードの分だけ移動。座標系において左は負の方向
            dx = self.speed

        if key_lst[pg.K_UP] and self.in_air == False:
            # Y軸方向の速度
            self.vel_y = -11
			# 空中フラグを更新
            self.in_air = True
            
		# 重力を適用。Y軸方向の速度に重力を加える。この重力は重力速度である。単位時間あたりの速度と考えるので力をそのまま速度に足して良い。
        self.vel_y += GRAVITY
		# Y軸方向の速度が一定以上なら
        if self.vel_y > 10:
			# 速さはゼロになる
            self.vel_y
		# Y軸方向の微小な移動距離を更新.単位時間なので距離に速度を足すことができる
        dy += self.vel_y

        self.rect.move_ip([dx, dy])

        # 床との衝突判定
        if self.rect.bottom + dy > (HEIGHT/2-50)+300-5:
            dy = (HEIGHT/2-50)+300-5 - self.rect.bottom
			# 空中フラグを更新
            self.in_air = False
            self.rect.move_ip([0, dy])
        
        # 壁との衝突判定
        if self.rect.left < WIDTH/2-150+5 or WIDTH/2+150-5 < self.rect.right:  # 横判定
            dx = -dx
            self.rect.move_ip([dx, 0])

        if self.invincible:  # 無敵時間の設定
            if self.invincible_time == 0:
                self.invincible = False
                self.invincible_time = __class__.invincible_time
            else:
                self.invincible_time -= 1
                if self.invincible_time % 5 == 0:
                    screen.blit(self.image, self.rect)
        else:
            screen.blit(self.image, self.rect)


class HealthBar(pg.sprite.Sprite):
    """
    体力ゲージに関するクラス
    """
    def __init__(self, x: int, y: int, width: int, max: int, gpa: float):
        """
        引数1 x：表示するx座標
        引数2 y：表示するy座標
        引数3 width：体力ゲージの幅
        引数4 max：体力の最大値
        引数5 gpa：表示するgpaの値
        """
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.max = max # 最大HP
        self.hp = max # HP
        self.mark = int((self.width - 4) / self.max) # HPバーの1目盛り

        self.font = pg.font.Font(FONT_F, 28)
        # HPとgpa表示の設定
        self.label = self.font.render(f"GPA:{gpa:.1f}  HP ", True, (255, 255, 255))
        # 体力ゲージのバー表示の設定
        self.frame = Rect(self.x + 2 + self.label.get_width(), self.y, self.width, self.label.get_height())
        self.bar = Rect(self.x + 4 + self.label.get_width(), self.y + 2, self.width - 4, self.label.get_height() - 4)
        self.value = Rect(self.x + 4 + self.label.get_width(), self.y + 2, self.width - 4, self.label.get_height() - 4)

    def update(self):
        self.value.width = self.hp * self.mark

    def draw(self, screen: pg.Surface):
        pg.draw.rect(screen, (255, 0, 0), self.bar)
        pg.draw.rect(screen, (255, 255, 0), self.value)
        screen.blit(self.label, (self.x, self.y))
        # 現在のHPと最大HPの表示
        hp_text = self.font.render(f" {self.hp}/{self.max}", True, (255, 255, 255))
        screen.blit(hp_text, (self.x + self.width + 10 + self.label.get_width(), self.y))


class Dialogue(pg.sprite.Sprite):
    """
    選択画面時のセリフに関するクラス
    """
    def __init__(self) -> None:
        """
        引数なし
        """
        super().__init__()
        self.font = pg.font.Font(FONT, 35)
        self.txt = "＊ こうかとんがあらわれた！"
        self.txt_len = len(self.txt)
        self.index = 0

    def update(self, screen: pg.Surface,reset=None):
        """
        引数1 screen：画面Surface
        引数2 reset：画面切り替え時に戻す
        """
        if self.index < self.txt_len:
            self.index += 1
        if reset:
            self.index = 0
        rend_txt = self.font.render(self.txt[:self.index], True, (255, 255, 255))
        screen.blit(rend_txt, (40, HEIGHT/2-20))


class Choice(pg.sprite.Sprite):
    """
    選択肢に関するクラス
    """
    def __init__(self, ls: list[str], x: int, y: int):
        """
        引数1 ls：表示する選択肢のリスト
        引数2 x：表示するx座標
        引数3 y：表示するy座標
        """
        super().__init__()
        self.choice_ls = ls
        self.x = x
        self.y = y
        
        self.font = pg.font.Font(FONT_F, 40)
        self.index = 0  # 選択しているものの識別用 

        self.whle = 50  # 四角形との間の距離 
        self.width = (WIDTH - (self.whle*(len(ls)-1)) - 20)/len(ls)
        self.height = 70

        self.switch_voice = pg.mixer.Sound("./voice/switch_select.wav")
        
    def draw(self, screen: pg.Surface, atk = False):
        """
        選択肢を表示する
        引数1 screen：画面Surface
        """
        for i, choice in enumerate(self.choice_ls):
            rect = pg.Rect(
                self.x + (self.width + self.whle) * i, # 四角形を描く開始座標
                self.y, 
                self.width, 
                self.height
                )
            if atk:
                color = (248, 138, 52)
            elif i == self.index:
                color = (255, 255, 0)
            else:
                color = (248, 138, 52)
            pg.draw.rect(screen, color, Rect(rect), 5)
            txt = self.font.render(choice, True, color)
            txt_rect = txt.get_rect()
            txt_rect.center = rect.center
            screen.blit(txt, txt_rect)

    def update(self, key):
        """
        キー入力による選択肢の変更
        引数1 key：押されたキーの識別
        """
        if key == pg.K_LEFT:
            self.index = (self.index - 1) % len(self.choice_ls)  # 右端から左端へ
            self.switch_voice.play(0)
        elif key == pg.K_RIGHT:
            self.index = (self.index + 1) % len(self.choice_ls)  # 左端から右端へ
            self.switch_voice.play(0)
            
        
class AfterChoice:
    """
    選択肢を選んだあとの画面に関するクラス
    """
    def __init__(self, ls: list[str]):
        """
        引数1 ls：選択肢のリスト
        """
        self.x = 40
        self.y = HEIGHT/2-20

        self.font = pg.font.Font(FONT, 35)
        self.txt_ls = ls

    def draw(self, screen: pg.Surface):
        for i, choice in enumerate(self.txt_ls):
            rend_txt = self.font.render(choice, True, (255, 255, 255))
            screen.blit(rend_txt, (self.x, self.y))
            if i % 2 == 0:
                self.x = WIDTH/2 + 40
            else:
                self.x = 40
                self.y += 60


class AttackBar:
    """
    敵を攻撃するアタックバーに関する関数
    """
    img = pg.transform.rotozoom(
        pg.image.load("fig/Attack_Bar.png"),
        0,1.8
    )
    def __init__(self):
        """
        アタックバーの初期化
        """
        # アタックの確率バーの描画
        self.vx, self.vy = +40, 0
        self.rimg = pg.Surface((10, 300), pg.SRCALPHA)
        pg.draw.rect(self.rimg, (255, 255, 255), (0, 0, 20, 300))
        self.rrct = self.rimg.get_rect()
        self.rrct.center = (20, HEIGHT/2+100)

        # アタックバーの描画
        self.img = __class__.img
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = WIDTH/2, HEIGHT/2+100

    def update(self, screen: pg.Surface):
        """
        アタックバーを表示
        引数1 screen：画面Surface
        """
        screen.blit(self.img, self.rct)

        yoko, tate = check_bound(self.rrct, 15, WIDTH-15, HEIGHT/2-55, HEIGHT/2+255)
        if not yoko:
            self.vx *= -1
        self.rrct.move_ip(self.vx, self.vy)
        screen.blit(self.rimg, self.rrct)


class GameOver:
    """
    ゲームオーバー画面に関するクラス
    """
    def __init__(self, rand : int):
        self.font = pg.font.Font(FONT_F, 150)
        self.txt1 = "GAME"
        self.txt2 = "OVER"
        self.txt_mes = [
            "あきらめては　いけない...", 
            "あきらめては　ダメだ！",
            "たんいを　すてるな！",
            "しっかりしろ！",
            ]
        self.font2 = pg.font.Font(FONT, 50)
        self.txt3 = self.txt_mes[rand]
        self.txt_len = len(self.txt3)
        self.index = 0
        self.tmr = 0

    def update(self, screen: pg.Surface,reset=None):
        """
        引数1 screen：画面Surface
        引数2 reset：画面切り替え時に戻す
        """
        rend_txt1 = self.font.render(self.txt1, False, (255, 255, 255))
        txt_rect1  = rend_txt1.get_rect()
        txt_rect1.center = WIDTH/2, 2*HEIGHT/6
        screen.blit(rend_txt1, txt_rect1)
        rend_txt2 = self.font.render(self.txt2, False, (255, 255, 255))
        txt_rect2  = rend_txt2.get_rect()
        txt_rect2.center = WIDTH/2, 3*HEIGHT/6
        screen.blit(rend_txt2, txt_rect2)

        if reset:
            self.index = 0
            self.tmr = 0
        if self.tmr > 30:
            if self.index < self.txt_len:
                self.index += 1
            rend_txt3 = self.font2.render(self.txt3[:self.index], True, (255, 255, 255))
            txt_rect3  = rend_txt3.get_rect()
            txt_rect3.center = WIDTH/2, 4*HEIGHT/6
            screen.blit(rend_txt3, txt_rect3)
        self.tmr += 1


class BreakHeart:
    """
    ゲームオーバー時にハートを壊すことに関するクラス
    """
    himg = pg.transform.rotozoom(
        pg.image.load("fig/Undertale_hurt.png"), 
        0, 0.02
        ) 
    bimg = pg.transform.rotozoom(
        pg.image.load("fig/Undertale_breakhurt.png"), 
        0, 0.02
        ) 
    def __init__(self, x:int, y:int):
        """
        引数1 x：ハートの最終座標x
        引数2 y：ハートの最終座標y
        """
        self.himg = __class__.himg
        self.bimg = __class__.bimg
        self.rect1: pg.Rect = self.himg.get_rect()
        self.rect2: pg.Rect = self.bimg.get_rect()
        self.rect1.center = (x, y)
        self.rect2.center = (x, y)

        self.break_heart = pg.mixer.Sound("./voice/break_heart.wav")

        self.tmr = 0
    
    def update(self, screen: pg.Surface, reset=False):
        """
        引数1 screnn：画面Surface
        引数2 reset：れセット判定
        """
        if reset:
            self.tmr = 0
        if self.tmr < 20:
            screen.blit(self.himg, self.rect1)
        elif 20 == self.tmr:
            self.break_heart.play(0)
        elif 20 < self.tmr:
            screen.blit(self.bimg, self.rect2)
        self.tmr += 1
"""
以下にこうかとんが攻撃する内容についてのクラスを各自用意する
"""

def main():
    pg.display.set_caption("koukAtale")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    """
    ゲームのシーンを切り替えるための変数
    """
    scenechange = 1  # 0: タイトル, 1:ゲームプレイ, 2:ゲームオーバー 
    gameschange = 0  # 0：選択画面, 1：攻撃
    """
    以下クラスの初期化
    """
    kkton = Koukaton()
    heart = Heart((WIDTH/2, HEIGHT/2+100 ))
    # heart = HeartGrav((WIDTH/2, HEIGHT/2+100))
    dialog = Dialogue()
    gpa = random.uniform(1, 4)
    max_hp = int(gpa*20)
    hp = HealthBar(WIDTH/4, 5*HEIGHT/6, max_hp+4, max_hp, gpa)
    choice_ls = ["たたかう", 
                 "こうどう", 
                 "アイテム", 
                 "みのがす"]
    choice = Choice(choice_ls, 10, HEIGHT - 80)
    attack_bar = AttackBar()
    gameov = GameOver(random.randint(0, 3))
    # これ以下に攻撃のクラスを初期化する

    """
    以下それぞれのシーンのタイマーを用意
    もし用意したければここに追加してください
    """
    clock = pg.time.Clock()  # time
    select_tmr = 0  # 選択画面時のタイマーの初期値
    attack_tmr = 0  # 攻撃中のタイマーの初期値
    gameover_tmr = 0  # gameover中のタイマー
    """
    効果音やBGMの変数を用意
    """
    pygame.mixer.init()
    select_voice = pg.mixer.Sound("./voice/snd_select.wav")
    attack_voice = pg.mixer.Sound("./voice/attack.wav")
    sound = pg.mixer.Sound("./sound/Megalovania.mp3")
    sound.play(-1)
    """
    その他必要な初期化
    """
    attack_num = 1  # 攻撃の種類に関する変数
    attack_rand = 0  # ランダムにこうかとんの攻撃を変えるための変数

    # ゲーム開始
    while True:
        """
        for文内では基本的にゲームのシーンの切り替えと
        必要に応じてクラスの呼び出しに使用している
        """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            elif event.type == pg.KEYDOWN:
                if gameschange == 0:  
                    """
                    選択画面での処理
                    """
                    choice.update(event.key)
                    if event.key == pg.K_RETURN:  # エンターキーを押されたら
                        if choice.index == 0:  # こうげきを選択していたら
                            select_voice.play(0)
                            gameschange = 1
                        elif choice.index == 1:  # こうどうを選択していたら
                            pass
                        elif choice.index == 2:  # アイテムを選択していたら
                            pass
                        elif choice.index == 3:  # みのがすを選択していたら
                            pass
                elif gameschange == 1:  
                    """
                    攻撃相手を選択する画面での処理
                    """    
                    if event.key == pg.K_ESCAPE:
                        gameschange = 0
                    elif event.key == pg.K_RETURN:
                        select_voice.play(0)
                        gameschange = 2
                elif gameschange == 2:
                    """
                    アタックバーが表示されている画面での処理
                    """
                    if event.key == pg.K_RETURN:
                        attack_voice.play(0)
                        attack_rand = random.randint(0, attack_num)  # 攻撃をランダムに選択
                        gameschange = 3

        screen.fill((0,0,0))  # 背景を描画

        if scenechange == 1:
            """
            ゲームプレイシーン
            """
            if gameschange == 0:  # 選択画面
                attack_tmr = 0
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)  # 大枠を描画
                kkton.update(screen)  # こうかとんを描画
                dialog.update(screen)  # 「こうかとんがあらわれた！」を表示
                hp.draw(screen)  # 残り体力を描画
                hp.update()  # 残り体力を更新
                choice.draw(screen)  # 
                select_tmr += 1
            
            elif gameschange == 1:  # こうげきを選択した場合
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)  # 大枠を描画
                afterchoice = AfterChoice(["＊　こうかとん"])  # 攻撃相手のリストを渡す
                afterchoice.draw(screen)  # 渡したリストを表示
                kkton.update(screen)  # こうかとんの表示
                hp.draw(screen)  # 残り体力の描画
                hp.update()  # 残り体力の更新
                choice.draw(screen)  # 選択肢の更新

            elif gameschange == 2:  # アタックバー画面
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)  # 大枠を描画
                kkton.update(screen)  # こうかとんの表示
                attack_bar.update(screen)  # アタックバーの表示
                hp.draw(screen)  # 残り体力の表示
                hp.update()  # 残り体力の更新
                choice.draw(screen)  # 選択肢の表示

            elif gameschange == 3:  # 攻撃される画面
                """
                以下にこうかとんの攻撃画面が表示される。
                攻撃の描画やあたり判定などはここで行うこと
                """
                pg.draw.rect(screen,(255,255,255), Rect(WIDTH/2-150, HEIGHT/2-50, 300, 300), 5)
                if hp.hp <= 0:
                    """
                    hpが0になったらゲームオーバー画面へと変更するようにしている
                    """
                    sound.stop()
                    breakheart = BreakHeart(heart.rect.x, heart.rect.y)
                    scenechange = 2

                if attack_rand == 0:
                    """
                    いかに攻撃の描画を行う
                    """
                    pass
                
                """
                クラスの更新を行う
                """
                # 以下に攻撃に関するクラスの更新

                kkton.update(screen)
                key_lst = pg.key.get_pressed()
                heart.update(key_lst, screen)
                hp.draw(screen)
                choice.draw(screen, True)
                hp.update()
                if attack_tmr > 300: # 選択画面に戻る
                    """
                    タイマーが300以上になったら選択画面に戻るように設定している。
                    """
                    dialog.update(screen, True)
                    # 初期化
                    heart = Heart((WIDTH/2, HEIGHT/2+100))
                    gameschange = 0

                attack_tmr += 1

        elif scenechange == 2:
            """
            ゲームオーバーシーン
            死んだ際
            """
            if gameover_tmr < 50:
                breakheart.update(screen)
            elif gameover_tmr == 50:
                sound = pg.mixer.Sound("./sound/gameover.mp3")
                sound.play(-1)
            elif 50 < gameover_tmr <= 400:
                gameov.update(screen)
            elif gameover_tmr > 400:
                sound.stop()
                heart = Heart((WIDTH/2, HEIGHT/2+100))
                # beams.update(screen, True)
                # barrages.update(True)
                hp =HealthBar(WIDTH/4, 5*HEIGHT/6, max_hp+4, max_hp, gpa)
                gameover_tmr = 0
                gameov.update(screen, True)
                sound = pg.mixer.Sound("./sound/Megalovania.mp3")
                sound.play(-1)
                gameschange = 0
                scenechange = 1
            gameover_tmr += 1
                
        pg.display.update()
        clock.tick(30)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
