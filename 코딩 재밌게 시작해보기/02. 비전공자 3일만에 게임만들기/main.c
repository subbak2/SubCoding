/*
 * 2대1 프로야구
 * 투수 두 명(왼쪽 Pitcher1, 오른쪽 Pitcher2)이 던지는 공을 쳐서 점수를 모으는 게임.
 * 3아웃이 되거나 5000점을 넘기면 끝난다.
 *
 * 키: 2 왼쪽, 4 오른쪽, 1 위, 3 아래
 *     5 일반치기, 6 당겨치기, 7 밀어치기, 8 홈런(게이지가 가득 찼을 때)
 */
#include "./Image/splash.h"
#include "./Image/nsplash1.h"
#include "./Image/nsplash2.h"
#include "./Image/nsplash3.h"
#include "./Image/nsplash4.h"
#include "./Image/nsplash5.h"
#include "./Image/nsplash6.h"
#include "./Image/background.h"
#include "./Image/player.h"
#include "./Image/player_bat.h"
#include "./Image/pitcher1.h"
#include "./Image/pitcher2.h"
#include "./Image/lose.h"
#include "./Image/homerun_effect.h"
#include "./Image/homerun_effect2.h"
#include "./Image/ball.h"
#include "./Image/ending.h"


#define BLACK	0x0000
#define WHITE	0xfffe
#define BLUE	0x003e
#define GREEN	0x07c0
#define RED		0xf800
#define YELLOW	0xffc1

enum key{C1, C1_, D1, D1_, E1, F1, F1_, G1, G1_, A1, A1_, B1, C2, C2_, D2, D2_, E2, F2, F2_, G2, G2_, A2, A2_, B2};
enum note{N16, N8, N4, N2, N1};

/* 키 번호 */
#define KEY_UP			1
#define KEY_LEFT		2
#define KEY_DOWN		3
#define KEY_RIGHT		4
#define KEY_HIT			5	/* 일반치기 */
#define KEY_PULL		6	/* 당겨치기 */
#define KEY_PUSH		7	/* 밀어치기 */
#define KEY_HOMERUN		8	/* 홈런 */

/* 친 공(Player_ball)의 ball_flag: 0 대기, 1~4 친 방식 */
#define HIT_NORMAL		1
#define HIT_PULL		2
#define HIT_PUSH		3
#define HIT_HOMERUN		4

#define HOMERUN_GAUGE_MAX	20
#define STRIKE_ZONE_BOTTOM	238	/* 투수 공이 이 아래로 가면 스트라이크 */

/* 화면 아무 곳에 그리고 아무 키나 누를 때까지 기다린다 */
#define SHOW_AND_WAIT(image) \
	do { \
		Lcd_Draw_BMP(0, 0, image); \
		while(!Key_Get_Pressed()); \
		Timer4_Delay(500); \
	} while(0)


void Two_vs_one(void);

/* 시작 화면 음악 {음, 길이} */
static const int intro_melody[][2] = {
	{F2_, N8}, {E2, N8}, {F2, N8}, {G2_, N8}, {A2, N4}, {A2, N8}, {E2, N4}, {A2, N4}, {B2, N8}, {B2, N2},
	{A2, N8}, {G2_, N8}, {A2, N8}, {A2, N2}, {G2_, N8}, {A2, N8}, {B2, N2}, {B2, N8}, {A2, N8}, {G2_, N8}, {F2_, N4},
};

static void Play_Melody(const int melody[][2], int count)
{
	int i;
	for (i = 0; i < count; i++) Timer3_Buzzer_Beep(melody[i][0], melody[i][1]);
}

void User_Main(void)
{
	srand(RTC_Get_Time());

	Lcd_Control_Brightness(5);
	Lcd_Select_Buffer_Mode(LAYER_MODE);
	Lcd_Select_Draw_Frame_Buffer(0);
	Lcd_Select_Display_Frame_Buffer(0);
	Lcd_Clr_Screen(BLACK);
	Lcd_Draw_BMP(0, 0, splash);

	Uart_Printf("===================================================\n");
	Uart_Printf("	 아무 버튼이나 누르면 게임을 시작합니다.   	\n");
	Uart_Printf("             	2대1 프로야구                 	\n");
	Uart_Printf("===================================================\n");
	Uart_Printf(">> ");

	Play_Melody(intro_melody, sizeof(intro_melody) / sizeof(intro_melody[0]));

	while(!Key_Get_Pressed());
	Two_vs_one();
}

struct Score
{
	int timer;
	char game_strike;
	char game_out;
	int game_score;
	int speed_step;
	int player_curve_step;
	int pitcher1_curve_step;
	int player_homerun;		/* 홈런 게이지 0~20 */
	int score_factor;
};

struct Score Jebal_init = {0, 0, 0, 0, 19, 0, 0, 0, 0};
struct Score Jebal;

struct Thing
{
	int timer;
	int move_flag;		/* 1이면 다음 그리기 때 다시 그린다 */
	int pos[2];
	int pos_init[2];
	int pos_back[2];	/* 지우기용 직전 위치 */
	int size[2];
	unsigned short color;
	int speed_step;
	int move_step;
	int ball_flag;
	int cd_flag;		/* 충돌(공이 배트에 닿음) 표시 */
};

struct Thing Player_init = {0,1,{43,192},{43,192},{43,192},{24,48},BLACK, 1, 3, 0, 0};
struct Thing Pitcher1_init = {0,1,{77,60},{77,60},{77,60},{16,45},BLACK, 15, 5, 0, 0};
struct Thing Pitcher1_ball_init = {0,1,{318,10},{318,10},{318,10},{6,6}, YELLOW, 45, 1, 0, 0};
struct Thing Player_ball_init = {0,1,{318,10},{318,10},{318,10},{6,6}, YELLOW, 28, 1, 0, 0};

struct Thing Pitcher2_init = {0,1,{220,60},{220,60},{220,60},{16,45},BLACK, 20, 3, 0, 0};
struct Thing Pitcher2_ball_init = {0,1,{318,10},{318,10},{318,10},{6,6}, YELLOW, 80, 1, 0, 0};
struct Thing Player_ball2_init = {0,1,{318,10},{318,10},{318,10},{6,6}, YELLOW, 35, 1, 0, 0};

struct Thing Player;
struct Thing Pitcher1;
struct Thing Pitcher1_ball;	/* Pitcher1이 던진 공 */
struct Thing Player_ball;	/* Pitcher1의 공을 쳐서 날아가는 공 */
struct Thing Pitcher2;
struct Thing Pitcher2_ball;
struct Thing Player_ball2;

void Game_Start(void)
{
	Jebal = Jebal_init;
	Player = Player_init;
	Pitcher1 = Pitcher1_init;
	Pitcher1_ball = Pitcher1_ball_init;
	Player_ball = Player_ball_init;
	Pitcher2 = Pitcher2_init;
	Pitcher2_ball = Pitcher2_ball_init;
	Player_ball2 = Player_ball2_init;

	Lcd_Clr_Screen(BLACK);
	SHOW_AND_WAIT(nsplash1);
	SHOW_AND_WAIT(nsplash2);
	SHOW_AND_WAIT(nsplash3);
	SHOW_AND_WAIT(nsplash4);
	SHOW_AND_WAIT(nsplash5);
	SHOW_AND_WAIT(nsplash6);
	Lcd_Draw_BMP(0, 0, background);
	Timer0_Repeat(18);
}

/* 배트를 휘두르는 모습을 잠깐 보여 주고 점수와 게이지를 올린다 */
void contact(void)
{
	Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player_bat);
	Timer4_Delay(50);
	Lcd_Draw_BMP2(Player.pos_back[0], Player.pos_back[1], 100, 60, background);
	Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
	Jebal.game_score+=10;
	Jebal.pitcher1_curve_step +=2;
	if (Jebal.pitcher1_curve_step>=6) Jebal.pitcher1_curve_step = 0;
	if (Jebal.player_homerun<HOMERUN_GAUGE_MAX) Jebal.player_homerun+=1;
}

/* ---------- 충돌 ---------- */

static void Draw_Count_Lamps(void)
{
	if(Jebal.game_strike == 1)  Lcd_Draw_Bar(276, 189, 289, 202, GREEN);
	if(Jebal.game_strike == 2)
	{
		Lcd_Draw_Bar(276, 189, 289, 202, GREEN);
		Lcd_Draw_Bar(301, 189, 314, 202, GREEN);
	}
	if(Jebal.game_out == 1)		Lcd_Draw_Bar(276, 220, 289, 233, RED);
	if(Jebal.game_out == 2)
	{
		Lcd_Draw_Bar(276, 220, 289, 233, RED);
		Lcd_Draw_Bar(301, 220, 314, 233, RED);
	}
}

/* 투수 공이 배트 영역(가로 25~60, 세로 0~bat_bottom)에 들어오면 칠 수 있는 상태로 만든다 */
static void Check_Bat_Contact(struct Thing *pitch, int bat_bottom)
{
	int ball_right = pitch->pos[0] + pitch->size[0];
	int ball_bottom = pitch->pos[1] + pitch->size[1];

	if(pitch->ball_flag == 0 || pitch->cd_flag != 0) return;
	if(!(pitch->pos[0] > Player.pos[0] + 25 && ball_right < Player.pos[0] + 60)) return;
	if(!(ball_bottom > Player.pos[1] && ball_bottom < Player.pos[1] + bat_bottom)) return;

	pitch->move_flag = 1;
	Player.move_flag = 1;

	Player.timer = 0;
	pitch->timer = 0;

	pitch->cd_flag = 1;
	Player.cd_flag = 1;
}

void collision_detect2(void)
{
	Draw_Count_Lamps();
	Check_Bat_Contact(&Pitcher1_ball, 47);
	Check_Bat_Contact(&Pitcher2_ball, 50);
}

/* ---------- 그리기 ---------- */

/* 점수 구간(1000~1200, 2000~2200 ... 5000~5200)에서 Pitcher2 투구 간격을 줄인다 */
static void Speed_Up_Pitcher2(void)
{
	int level;
	for (level = 1; level <= 5; level++)
	{
		if(Jebal.game_score >= 1000*level && Jebal.game_score <= 1000*level + 200)
		{
			Jebal.score_factor++;
			if (Jebal.score_factor >=3) Jebal.score_factor=0;
			Pitcher2.speed_step -= (15*Jebal.score_factor);
		}
	}
}

/* 투수 공이 스트라이크 존 아래로 지나가면 스트라이크, 3스트라이크면 아웃 */
static void Check_Strike(struct Thing *pitch, int speed_up)
{
	if(pitch->pos[1] <= STRIKE_ZONE_BOTTOM) return;

	pitch->ball_flag = 0;
	if (Jebal.timer <= Jebal.speed_step) return;

	Jebal.timer = 0;
	Jebal.game_strike++;
	if (speed_up) Speed_Up_Pitcher2();

	if(Jebal.game_strike == 1)  Lcd_Draw_Bar(276, 189, 289, 202, GREEN);
	if(Jebal.game_strike == 2)  Lcd_Draw_Bar(301, 189, 314, 202, GREEN);
	if(Jebal.game_strike == 3)
	{
		Jebal.game_out++;
		Jebal.game_strike = 0;
		Lcd_Draw_BMP2(275, 185, 45, 20, background);
	}
}

/* 친 공을 화면에서 지운다 (파울·1루타는 15x15, 그 밖은 6x6) */
static void Erase_Batted_Ball(struct Thing *batted, int size)
{
	Lcd_Draw_BMP2(batted->pos[0], batted->pos[1], size, size, background);
	batted->ball_flag = 0;
	if (size == 15)
	{
		Lcd_Draw_BMP2(batted->pos_back[0], batted->pos_back[1], 15, 15, background);
		Lcd_Draw_BMP2(batted->pos[0], batted->pos[1], 15, 15, background);
	}
}

static void Homerun_Celebration(struct Thing *batted)
{
	Lcd_Draw_BMP(0, 0, homerun_effect);
	Timer3_Buzzer_Beep(C1,N16);
	Lcd_Draw_BMP(0, 0, homerun_effect2);
	Timer3_Buzzer_Beep(E1,N16);
	Lcd_Draw_BMP(0, 0, homerun_effect);
	Timer3_Buzzer_Beep(G1,N16);
	Lcd_Draw_BMP(0, 0, homerun_effect2);
	Timer3_Buzzer_Beep(C2,N8);
	batted->move_flag = 0;
	Lcd_Draw_BMP(0, 0, homerun_effect);
	Timer3_Buzzer_Beep(G1,N16);
	batted->move_flag = 1;
	Lcd_Draw_BMP(0, 0, homerun_effect2);
	Timer3_Buzzer_Beep(C2,N8);
	Lcd_Draw_BMP(0, 0, background);
	Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
}

/* 친 공이 어디까지 갔는지 보고 파울·안타·홈런을 판정한다 */
static void Judge_Batted_Ball(struct Thing *batted)
{
	int x = batted->pos[0];
	int y = batted->pos[1];
	int gauge = Jebal.player_homerun;

	if(y > 110 && (x < 7 || x > 292) && batted->ball_flag != 0)
	{
		Erase_Batted_Ball(batted, 15);
		Lcd_Printf(190,7,WHITE,BLACK,1,1,"파울!");
		if(Jebal.game_strike < 2) Jebal.game_strike++;
		Jebal.game_score-=10;
	}

	if(y < (140 + Jebal.pitcher1_curve_step) && gauge < 10 && batted->ball_flag != 0)
	{
		Erase_Batted_Ball(batted, 15);
		Lcd_Printf(190,7,WHITE,BLACK,1,1,"1루타");
	}

	if(y < 40 && gauge >= 10 && gauge <= HOMERUN_GAUGE_MAX && gauge%3 != 0 && batted->ball_flag != HIT_HOMERUN)
	{
		Erase_Batted_Ball(batted, 6);
		Lcd_Printf(190,7,WHITE,BLACK,1,1,"2루타");
		Jebal.game_score+=20;
	}

	if(y < 20 && gauge <= HOMERUN_GAUGE_MAX && batted->ball_flag != 0 && batted->ball_flag != HIT_HOMERUN)
	{
		Erase_Batted_Ball(batted, 6);
		Lcd_Printf(190,7,WHITE,BLACK,1,1,"3루타");
		Jebal.game_score+=40;
	}

	if(y < 7 && batted->ball_flag == HIT_HOMERUN)
	{
		Erase_Batted_Ball(batted, 6);
		Lcd_Printf(190,7,WHITE,BLACK,1,1,"홈런!");
		Jebal.game_score+=190;
		Jebal.player_homerun =0;
		Homerun_Celebration(batted);
	}
}

/* 움직인 것을 직전 위치에서 지우고 새 위치에 그린다 */
static void Redraw_Ball(struct Thing *b)
{
	if(b->move_flag == 0) return;
	Lcd_Draw_BMP2(b->pos_back[0], b->pos_back[1], 6, 6, background);
	Lcd_Draw_BMP(b->pos[0], b->pos[1], ball);
	b->move_flag = 0;
}

/* 투수 한 명분(타자·투수·던진 공·친 공)을 그린다. side 1 = Pitcher1, 2 = Pitcher2 */
static void Draw_Side(int side)
{
	struct Thing *pitcher = (side == 1) ? &Pitcher1 : &Pitcher2;
	struct Thing *pitch   = (side == 1) ? &Pitcher1_ball : &Pitcher2_ball;
	struct Thing *batted  = (side == 1) ? &Player_ball : &Player_ball2;

	if(Player.move_flag != 0 || pitch->timer == 0)
	{
		Lcd_Draw_BMP2(Player.pos_back[0], Player.pos_back[1], 50, 76, background);
		Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
		Player.move_flag = 0;
	}
	if(pitcher->move_flag != 0)
	{
		Lcd_Draw_BMP2(pitcher->pos_back[0], pitcher->pos_back[1], (side == 1) ? 25 : 40, 55, background);
		Lcd_Draw_BMP(pitcher->pos[0], pitcher->pos[1], (side == 1) ? pitcher1 : pitcher2);
		pitcher->move_flag = 0;
	}

	Check_Strike(pitch, side == 1);
	Redraw_Ball(pitch);

	Judge_Batted_Ball(batted);
	Redraw_Ball(batted);
}

void Draw_Thing(void)
{
	Draw_Side(1);
	Draw_Side(2);
}

/* ---------- 타자 ---------- */

/* 타자를 한 칸 움직인다. axis 0 = 가로, 1 = 세로 */
static void Step_Player(int axis, int direction)
{
	Player.timer = 0;
	Player.pos_back[axis] = Player.pos[axis];
	Player.pos[axis] = Player.pos_back[axis] + direction * Player.move_step;
	Player.move_flag = 1;
	if (axis == 0 && ++Jebal.pitcher1_curve_step >=6) Jebal.pitcher1_curve_step = 0;
}

static void Charge_Homerun_Gauge(void)
{
	if (Jebal.player_homerun<=15) Jebal.player_homerun+=5;
	else Jebal.player_homerun=HOMERUN_GAUGE_MAX;
}

/* 배트를 휘두른다. 배트에 닿아 있던 투수 공은 hit_type 방향으로 날아간다 */
static void Swing(int hit_type, int curve_add, int curve_limit, int charge_gauge)
{
	contact();
	Player.cd_flag = 0;
	if (Pitcher1_ball.cd_flag == 1)
	{
		Pitcher1_ball.cd_flag = 0;
		Pitcher1_ball.ball_flag = 0;
		Player_ball.ball_flag = hit_type;
	}
	if (Pitcher2_ball.cd_flag == 1)
	{
		Pitcher2_ball.cd_flag = 0;
		Pitcher2_ball.ball_flag = 0;
		Player_ball2.ball_flag = hit_type;
	}
	Jebal.player_curve_step+=curve_add;
	if (Jebal.player_curve_step >= curve_limit) Jebal.player_curve_step = 0;
	if (charge_gauge) Charge_Homerun_Gauge();
}

void Move_Player(void)
{
	int key = 0;
	Player.timer++;

	key = Key_Get_Pressed();

	switch(key)
	{
	case KEY_LEFT:
		if(Player.pos_back[0]>50) Step_Player(0, -1);
		break;
	case KEY_RIGHT:
		if(Player.pos_back[0]<175) Step_Player(0, +1);
		break;
	case KEY_UP:
		if(Player.pos_back[1]>180) Step_Player(1, -1);
		break;
	case KEY_DOWN:
		if(Player.pos_back[1]<192) Step_Player(1, +1);
		break;
	case KEY_HIT:
		if(Player.cd_flag == 1) Swing(HIT_NORMAL, 1, 4, Player.pos[0]>=150);
		break;
	case KEY_PULL:
		if(Player.cd_flag == 1) Swing(HIT_PULL, 2, 4, Player.pos[0]<=115);
		break;
	case KEY_PUSH:
		if(Player.cd_flag == 1) Swing(HIT_PUSH, 1, 5, Player.pos[0]>150);
		break;
	case KEY_HOMERUN:
		if(Player.cd_flag == 1 && Jebal.player_homerun == HOMERUN_GAUGE_MAX) Swing(HIT_HOMERUN, 2, 5, 0);
		break;
	}
}

/* ---------- 투수와 공 ---------- */

/* 투수가 direction 쪽으로 걷다가 limit에 닿으면 처음 자리로 돌아간다 */
static void Walk_Pitcher(struct Thing *pitcher, int direction, int limit)
{
	int reached = (direction > 0) ? (pitcher->pos[0] >= limit) : (pitcher->pos[0] <= limit);

	if ((pitcher->timer >= pitcher->speed_step) && !reached)
	{
		pitcher->timer = 0;
		pitcher->pos_back[0] = pitcher->pos[0];
		pitcher->pos[0] = pitcher->pos[0] + direction * pitcher->move_step;
		pitcher->move_flag = 1;
	}
	reached = (direction > 0) ? (pitcher->pos[0] >= limit) : (pitcher->pos[0] <= limit);
	if (reached)
	{
		pitcher->timer = 0;
		pitcher->pos_back[0] = pitcher->pos[0];
		pitcher->pos[0] = pitcher->pos_init[0];
		pitcher->move_flag = 1;
	}
}

/* 던지기 전 공은 투수 손에 있다가 speed_step이 지나면 던진다 */
static void Ready_Pitch(struct Thing *pitch, struct Thing *pitcher)
{
	if(pitch->ball_flag != 0) return;

	pitch->pos_init[0] = pitcher->pos[0];
	pitch->pos_init[1] = pitcher->pos[1];
	pitch->pos_back[0] = pitch->pos_init[0];
	pitch->pos_back[1] = pitch->pos_init[1];
	pitch->pos[0] = pitch->pos_init[0];
	pitch->pos[1] = pitch->pos_init[1];

	if (pitch->timer >= pitch->speed_step)
	{
		pitch->timer = 0;
		pitch->pos_back[1] = pitch->pos[1];
		pitch->ball_flag = 1;
	}
}

/* Pitcher1 공: 가운데(90~120)에서 휘고, 아래(160~)에서 빨라진다. 점수가 3의 배수면 직구 */
static void Fly_Pitch1(void)
{
	struct Thing *b = &Pitcher1_ball;
	int step = b->move_step;

	if (b->ball_flag != 1) return;

	b->pos_back[0] = b->pos[0];
	b->pos_back[1] = b->pos[1];
	if (Jebal.game_score%3 !=0)
	{
		if (b->pos_back[0] < 120 && b->pos_back[0] > 90)
			b->pos[0] += ((Jebal.pitcher1_curve_step+4)%5-2)*step;
		else
			b->pos[0] += step;

		if (b->pos_back[1] > 160) b->pos[1] += 2*step;
		else b->pos[1] += step;
	}
	else
	{
		b->pos[0] += step;
		b->pos[1] += 2*step;
	}
	b->move_flag = 1;
}

/* 화면 가장자리(100 이하, 240 초과)에 있는 공을 가운데 쪽으로 한 칸 */
static void Drift_To_Center(struct Thing *b)
{
	if (b->pos[0] >240) b->pos[0] -= b->move_step;
	else if (b->pos[0] <=100) b->pos[0] += b->move_step;
}

/* Pitcher2 공: 140~220에서 왼쪽으로 휘고, 아래(170~)에서는 가운데로 모인다. 점수가 6의 배수면 직구 */
static void Fly_Pitch2(void)
{
	struct Thing *b = &Pitcher2_ball;
	int step = b->move_step;

	if (b->ball_flag != 1) return;

	b->pos_back[0] = b->pos[0];
	b->pos_back[1] = b->pos[1];
	if (Jebal.game_score%6 !=0)
	{
		if (b->pos[0] > 140 && b->pos[0] <= 220)
			b->pos[0] -= ((Jebal.pitcher1_curve_step+4)%5)*step;

		if (b->pos[1] > 170)
		{
			Drift_To_Center(b);
			b->pos[1] += step;
		}
		else b->pos[1] += ((Jebal.pitcher1_curve_step+4)%5+1)*step;
	}
	else
	{
		Drift_To_Center(b);
		b->pos[1] += 2*step;
	}
	b->move_flag = 1;
}

/* 친 공: 치기 전에는 배트 끝에 붙어 있고, 친 뒤에는 친 방식대로 날아간다 */
static void Fly_Batted_Ball(struct Thing *b)
{
	int step = b->move_step;

	if(b->ball_flag == 0)
	{
		b->pos_init[0] = (Player.pos[0]+55);
		b->pos_init[1] = (Player.pos[1]+15);
		b->pos_back[0] = b->pos_init[0];
		b->pos_back[1] = b->pos_init[1];
		b->pos[0] = b->pos_init[0];
		b->pos[1] = b->pos_init[1];
		return;
	}
	if (b->ball_flag < HIT_NORMAL || b->ball_flag > HIT_HOMERUN) return;

	b->pos_back[1] = b->pos[1];
	b->pos_back[0] = b->pos[0];
	switch (b->ball_flag)
	{
	case HIT_NORMAL:
		b->pos[0] += ((Jebal.player_curve_step%3)-1)*step;
		b->pos[1] -= 3*step;
		break;
	case HIT_PULL:
		b->pos[0] -= (2+(Jebal.player_curve_step%4))*step;
		b->pos[1] -= 3*step;
		break;
	case HIT_PUSH:
		b->pos[0] += (1+(Jebal.player_curve_step%4))*step;
		b->pos[1] -= 2*step;
		break;
	case HIT_HOMERUN:
		b->pos[0] += ((Jebal.pitcher1_curve_step%5)-2)*step;
		b->pos[1] -= 4*step;
		break;
	}
	b->move_flag = 1;
}

void Move_Pitchers(void)
{
	Pitcher1.timer++;
	Pitcher1_ball.timer++;
	Walk_Pitcher(&Pitcher1, +1, 120);
	Ready_Pitch(&Pitcher1_ball, &Pitcher1);
	Fly_Pitch1();
	Fly_Batted_Ball(&Player_ball);

	Pitcher2.timer++;
	Pitcher2_ball.timer++;
	Walk_Pitcher(&Pitcher2, -1, 185);
	Ready_Pitch(&Pitcher2_ball, &Pitcher2);
	Fly_Pitch2();
	Fly_Batted_Ball(&Player_ball2);
}

void Move_Character(void)
{
	if(Timer0_Check_Expired())
	{
		Jebal.timer++;
		Move_Player();
		Move_Pitchers();
	}
}

/* ---------- 게임 ---------- */

void Game_lose(void)
{
	Lcd_Clr_Screen(BLACK);
	if (Jebal.game_score<5000)
	{
		Lcd_Draw_BMP(0, 0, lose);
		Lcd_Printf(200,110,WHITE,BLACK,1,2,"  SCORE : %d ", Jebal.game_score);
	}
	else
	{
		Lcd_Draw_BMP(0, 0, ending);
	}
}

void Two_vs_one(void)
{
	Lcd_Set_Shape_Mode(1,YELLOW);
	Game_Start();
	Draw_Thing();

	for(;;)
	{
		collision_detect2();
		Move_Character();
		Draw_Thing();
		Lcd_Printf(150,7,WHITE,BLACK,1,1,"%d", Jebal.game_score);
		Lcd_Draw_Bar(27, 235, 40, 235-(3*Jebal.player_homerun), BLUE);
		if (Jebal.player_homerun == 0) Lcd_Draw_BMP2(26, 170, 20, 70, background);
		if (Jebal.game_out == 3) break;
		if (Jebal.game_score > 5000) break;
	}
	Game_lose();
	Timer4_Delay(300);
	while(!Key_Get_Pressed());
}
