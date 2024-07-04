import os
import sys
import pygame as pg
from pygame.locals import *
import pygame.mixer
import time
import random
import math

# グローバル変数
WIDTH, HEIGHT = 1024, 768 # ディスプレイサイズ
FONT = "font/JF-Dot-MPlusS10.ttf"  # ドット文字細目
FONT_F = "font/JF-Dot-MPlusS10B.ttf"  # ドット文字太目
GRAVITY = 0.75  #重力の大きさ。ジャンプした時に落ちる力。

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
    

class Koukaton(pg.sprite.Sprite):
    """
    こうかとんに関するクラス
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
		# ジャンプのフラグ
        self.jump = False
		# 空中にいるかどうかのフラグ
        self.in_air = True

        self.invincible = False

    def update(self, moving_left, moving_right, screen: pg.Surface):
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
        if moving_left:
			# スピードの分だけ移動。座標系において左は負の方向
            dx = -self.speed

		# 右に移動
        if moving_right:
			# スピードの分だけ移動。座標系において左は負の方向
            dx = self.speed

		#ジャンプ
		# ジャンプ中かつ空中フラグはまだFalse
        if self.jump == True and self.in_air == False:
			# Y軸方向の速度
            self.vel_y = -11
			# ジャンプのフラグを更新
            self.jump = False
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


class AttackBeam(pg.sprite.Sprite):
    """
    こうかとんの落単ビーム攻撃に関するクラス
    """
    def __init__(self, color: tuple[int, int, int],start_pos: tuple[int, int]):
        """
        引数に基づき攻撃Surfaceを生成する
        color：色
        start_pos：スタート位置
        """
        super().__init__()
        self.vx, self.vy = 0, +10

        self.font = pygame.font.Font(FONT, 18)
        self.label = self.font.render("落単", False, (50, 50, 50))
        self.frct = self.label.get_rect()
        self.frct.center = start_pos

        self.image = pg.Surface((100, 20), pg.SRCALPHA)
        pg.draw.rect(self.image, color, (0, 0, 100, 20))
        self.rect = self.image.get_rect()
        self.rect.center = start_pos        

    def update(self, screen: pg.Surface, reset=False):
        """
        引数1 screen：画面Surface
        """
        self.rect.move_ip(self.vx, self.vy)
        screen.blit(self.image, self.rect)
        self.frct.move_ip(self.vx, self.vy)
        screen.blit(self.label, self.frct)
        if check_bound1(self.rect) != (True, True) or reset:
            self.kill()  


class AttackBarrage(pg.sprite.Sprite):
    """
    弾幕攻撃に関するクラス
    """
    def __init__(self, kkton: "Koukaton", heart: "Heart", angle = 0):
        """
        引数1 kkton：こうかとん
        引数2 heart：攻撃対象のハート
        """
        super().__init__()
        rad = 10
        self.image = pg.Surface((2*rad, 2*rad))
        color = (255, 255, 255)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        
        # 弾幕を発射する場所からみた攻撃対象(heart)の方向を計算
        self.vx, self.vy = calc_orientation(kkton.rect, heart.rect)
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))

        self.rect.centerx = kkton.rect.centerx-40 # バックから出ているように調整
        self.rect.centery = kkton.rect.centery+kkton.rect.height//2-40
        self.speed = 10

    def update(self, reset=False):
        """
        弾幕を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 reset：resetしたいときにTrueにする
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound1(self.rect) != (True, True) or reset:
            self.kill()

class SettingBarrage(pg.sprite.Sprite):
    """
    弾幕生成に関するクラス
    """
    def __init__(self, num = 5):
        """
        引数1 num:弾幕の拡散量
        """
        super().__init__()
        self.num = num
        self.ang = []
    
    def update(self):
        step = range(-50, 51, (int(70/(self.num-1))))
        self.ang = [i+random.randint(-10,10) for i in step]

    def gen_barrage(self):
        return self.ang


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
        elif key == pg.K_RIGHT:
            self.index = (self.index + 1) % len(self.choice_ls)  # 左端から右端へ


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
        """
        self.himg = __class__.himg
        self.bimg = __class__.bimg
        self.rect1: pg.Rect = self.himg.get_rect()
        self.rect2: pg.Rect = self.bimg.get_rect()
        self.rect1.center = (x, y)
        self.rect2.center = (x, y)

        self.tmr = 0
    
    def update(self, screen: pg.Surface, reset=False):
        """
        """
        if reset:
            self.tmr = 0
        if self.tmr < 20:
            screen.blit(self.himg, self.rect1)
        elif 20 <= self.tmr:
            screen.blit(self.bimg, self.rect2)
        self.tmr += 1

    
def main():
    pg.display.set_caption("koukAtale")
    screen = pg.display.set_mode((WIDTH, HEIGHT))   
    # シーン状態の推移
    scenechange = 1  # 0: タイトル, 1:ゲームプレイ, 2:ゲームオーバー 
    gameschange = 0  # 0：選択画面, 1：攻撃
    # こうかとんの初期化
    kkton = Koukaton()
    # ハートの初期化
    # heart = Heart((WIDTH/2, HEIGHT/2+100 ))
    # 重力ハートの初期化
    heart = HeartGrav((WIDTH/2, HEIGHT/2+100))
    # 落単ビームの初期化
    beams = pg.sprite.Group()
    # 弾幕の初期化
    barrages = pg.sprite.Group()
    set_barrages = SettingBarrage() 
    # セリフに関する初期化
    dialog = Dialogue()
    # ヘルスバーに関する初期化
    gpa = random.uniform(1, 4)
    max_hp = int(gpa*20)
    hp =HealthBar(WIDTH/4, 5*HEIGHT/6, max_hp+4, max_hp, gpa) # maxの値はwidth-4を割り切れる数にする
    # 選択肢の初期化
    choice_ls = ["たたかう", 
                 "こうどう", 
                 "アイテム", 
                 "みのがす"]
    choice = Choice(choice_ls, 10, HEIGHT - 80)
    # アタックバーの初期化
    attack_bar = AttackBar()
    # GameOverの初期化
    gameov = GameOver(random.randint(0, 3))
    clock = pg.time.Clock()  # time
    select_tmr = 0  # 選択画面時のタイマーの初期値
    attack_tmr = 0  # 攻撃中のタイマーの初期値
    attack_rand = 0
    gameover_tmr = 0  # gameover中のタイマー

    # プレイヤーの進行方向のフラグ
    moving_left = False
    moving_right = False

    pygame.mixer.init()
    sound = pg.mixer.Sound("./sound/Megalovania.mp3")
    sound.play(-1)

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            elif event.type == pg.KEYDOWN:
                # 選択画面なら
                if gameschange == 0:  
                    choice.update(event.key)
                    if event.key == pg.K_RETURN:  # エンターキーを押されたら
                        if choice.index == 0:  # こうげきを選択していたら
                            gameschange = 1
                        elif choice.index == 1:  # こうどうを選択していたら
                            pass
                        elif choice.index == 2:  # アイテムを選択していたら
                            pass
                        elif choice.index == 3:  # みのがすを選択していたら
                            pass
                # 攻撃相手選択画面なら
                elif gameschange == 1:      
                    if event.key == pg.K_ESCAPE:
                        gameschange = 0
                    elif event.key == pg.K_RETURN:
                        gameschange = 2
                # アタックバーなら
                elif gameschange == 2:
                    if event.key == pg.K_RETURN:
                        attack_rand = random.randint(0, 1)
                        gameschange = 3

                if event.key == pygame.K_LEFT:
                    # 左移動フラグをTrue
                    moving_left = True
                if event.key == pygame.K_RIGHT:
                    # 右移動フラグをTrue
                    moving_right = True
                # wキーを押す、かつ、プレイヤーが生きている
                if event.key == pygame.K_UP:
                    # ジャンプフラグをTrue
                    heart.jump = True

            elif event.type == pg.KEYUP:
                if event.key == pg.K_LEFT:
                    # 左移動フラグをTrue
                    moving_left = False
                if event.key == pg.K_RIGHT:
                    # 右移動フラグをTrue
                    moving_right = False
        
        # 背景関連
        screen.fill((0,0,0))

        if scenechange == 1:  # 攻撃

            if gameschange == 0:  # 選択画面
                attack_tmr = 0
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                kkton.update(screen)
                dialog.update(screen)
                hp.draw(screen)
                hp.update()
                choice.draw(screen)
                select_tmr += 1

            elif gameschange == 1:  # こうげきを選択した場合
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                # 選択肢後の画面に関する初期化
                afterchoice = AfterChoice(["＊　こうかとん"])   
                kkton.update(screen)
                # 攻撃相手の選択画面
                afterchoice.draw(screen)
                # 体力バーの更新
                hp.draw(screen)
                hp.update()
                # 選択肢の更新
                choice.draw(screen)

            elif gameschange == 2:  # アタックバー画面
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                # こうかとんの表示
                kkton.update(screen)
                # アタックバーの表示
                attack_bar.update(screen)
                # hpの表示
                hp.draw(screen)
                hp.update()
                # 選択肢の表示
                choice.draw(screen)

            # elif gameschange == 3:  # 攻撃画面
            #     pg.draw.rect(screen,(255,255,255), Rect(WIDTH/2-150, HEIGHT/2-50, 300, 300), 5)
            #     if attack_rand == 0:
            #         # 落単ビームの発生
            #         if attack_tmr % 9 == 0:  # 一定時間ごとにビームを生成
            #             start_pos = (random.randint(WIDTH/2-100,WIDTH/2+100), 40)
            #             beams.add(AttackBeam((255, 255, 255), start_pos))
            #         # 落単との衝突判定
            #         if len(pg.sprite.spritecollide(heart, beams, False)) != 0:
            #             if heart.invincible == False:
            #                 hp.hp -= 1
            #                 heart.invincible = True
            #     elif attack_rand == 1:
            #         # 弾幕の発生
            #         if attack_tmr % 9 == 0:  # 一定時間ごとにビームを生成
            #             for ang in set_barrages.gen_barrage():
            #                 barrages.add(AttackBarrage(kkton, heart, ang))
            #         if len(pg.sprite.spritecollide(heart,barrages,False)) != 0:
            #             if heart.invincible == False:
            #                 hp.hp -= 1
            #                 heart.invincible = True

            #     # gameover判定
            #     if hp.hp <= 0:
            #         sound.stop()
            #         # brea
            #         breakheart = BreakHeart(heart.rect.x, heart.rect.y)
            #         scenechange = 2

            #     # こうかとんの表示
            #     kkton.update(screen)
            #     # キーに応じたハートの移動
            #     key_lst = pg.key.get_pressed()
            #     heart.update(key_lst, screen)
            #     # 攻撃終了判定
            #     if attack_tmr > 300: # 選択画面に戻る
            #         dialog.update(screen, True)
            #         # 初期化
            #         heart = Heart((WIDTH/2, HEIGHT/2+100))
            #         beams.update(screen, True)
            #         barrages.update(True)
            #         gameschange = 0
            #     # 落単の表示
            #     beams.update(screen) 
            #     # 弾幕の表示と更新
            #     barrages.update()
            #     barrages.draw(screen)
            #     set_barrages.update()
            #     # HPの表示と更新
            #     hp.draw(screen)
            #     hp.update()
            #     # 選択肢の表示
            #     choice.draw(screen, True)
            #     attack_tmr += 1

            elif gameschange == 3:  # 攻撃画面
                pg.draw.rect(screen,(255,255,255), Rect(WIDTH/2-150, HEIGHT/2-50, 300, 300), 5)
                if attack_rand == 0:
                    # 落単ビームの発生
                    if attack_tmr % 9 == 0:  # 一定時間ごとにビームを生成
                        start_pos = (random.randint(WIDTH/2-100,WIDTH/2+100), 40)
                        beams.add(AttackBeam((255, 255, 255), start_pos))
                    # 落単との衝突判定
                    if len(pg.sprite.spritecollide(heart, beams, False)) != 0:
                        if heart.invincible == False:
                            hp.hp -= 1
                            heart.invincible = True
                elif attack_rand == 1:
                    # 弾幕の発生
                    if attack_tmr % 9 == 0:  # 一定時間ごとにビームを生成
                        for ang in set_barrages.gen_barrage():
                            barrages.add(AttackBarrage(kkton, heart, ang))
                    if len(pg.sprite.spritecollide(heart,barrages,False)) != 0:
                        if heart.invincible == False:
                            hp.hp -= 1
                            heart.invincible = True

                # gameover判定
                if hp.hp <= 0:
                    sound.stop()
                    # brea
                    breakheart = BreakHeart(heart.rect.x, heart.rect.y)
                    scenechange = 2

                # こうかとんの表示
                kkton.update(screen)
                # キーに応じたハートの移動
                heart.update(moving_left, moving_right, screen)
                # 攻撃終了判定
                if attack_tmr > 300: # 選択画面に戻る
                    dialog.update(screen, True)
                    # 初期化
                    heart = HeartGrav((WIDTH/2, HEIGHT/2+100))
                    beams.update(screen, True)
                    barrages.update(True)
                    gameschange = 0
                # 落単の表示
                beams.update(screen) 
                # 弾幕の表示と更新
                barrages.update()
                barrages.draw(screen)
                set_barrages.update()
                # HPの表示と更新
                hp.draw(screen)
                hp.update()
                # 選択肢の表示
                choice.draw(screen, True)
                attack_tmr += 1
        
        # GameOver 
        elif scenechange == 2: 
            if gameover_tmr < 50:
                # heart.update(key_lst, screen)
                breakheart.update(screen)
            elif gameover_tmr == 50:
                sound = pg.mixer.Sound("./sound/gameover.mp3")
                sound.play(-1)
            elif 50 < gameover_tmr <= 400:
                gameov.update(screen)
            elif gameover_tmr > 400:
                sound.stop()
                heart = Heart((WIDTH/2, HEIGHT/2+100))
                beams.update(screen, True)
                barrages.update(True)
                hp =HealthBar(WIDTH/4, 5*HEIGHT/6, max_hp+4, max_hp, gpa)
                gameover_tmr = 0
                gameov.update(screen, True)
                sound = pg.mixer.Sound("./sound/Megalovania.mp3")
                sound.play(-1)
                gameschange = 0
                scenechange = 1
            gameover_tmr += 1
            

        # elif gameschange == 4:
        pg.display.update()
        clock.tick(30)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()