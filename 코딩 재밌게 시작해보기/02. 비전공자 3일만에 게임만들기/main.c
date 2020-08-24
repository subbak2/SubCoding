
#include "./Image/img01.h"
#include "./Image/img02.h"
#include "./Image/img03.h"
#include "./Image/img04.h"
#include "./Image/img05.h"
#include "./Image/shape.h"
#include "./Image/perfect.h"
#include "./Image/background.h"
#include "./Image/player.h"
#include "./Image/player_bat.h"
#include "./Image/pitcher1.h"
#include "./Image/pitcher2.h"
#include "./Image/bg_player.h"
#include "./Image/background_pit.h"
#include "./Image/lose.h"

const unsigned short * Disp[] = {img01, img02, img03, img04};

/* 5:5:5:I Color Definition */

#define BLACK	0x0000
#define WHITE	0xfffe
#define BLUE	0x003e
#define GREEN	0x07c0
#define RED	0xf800

void Basic_Graphics_Test(void);
void Special_Mode_Test(void);
void Font_Test(void);
void Brightness_Test(void);
void Key_Test(void);
void Buzzer_Test(void);
void Timer_Test(void);
void Simple_Example(void);
void Three_vs_one(void);

static char game_strike=0;
static char game_out=0;

struct Thing
{
	int timer;
	int move_flag;
	int pos[2];
	int pos_init[2];
	int pos_back[2];
	int size[2];
	unsigned short color;
	int speed_step;
	int move_step;
	int ball_flag;
	int cd_flag;
};

struct Thing Player = {0,1,{33,149},{33,149},{33,149},{24,47},BLACK, 1, 3, 0, 0};
struct Thing Pitcher1 = {0,1,{70,30},{70,30},{70,30},{16,45},BLACK, 10, 7, 0, 0};
struct Thing Pitcher1_ball = {0,1,{319,230},{319,230},{319,230},{4,4},BLACK, 18, 1, 0, 0};
struct Thing Player_ball = {0,1,{319,239},{319,239},{319,239},{4,4},RED, 9, 2, 0, 0};
/*
struct Thing Pitcher2 = {0,1,{220,30},{220,30},{220,30},{30,41},BLACK, 15, 4, 0, 0};
struct Thing Pitcher2_ball = {0,1,{319,239},{319,239},{319,239},{4,4},BLUE, 22, 1, 0, 0};
struct Thing Player2_ball = {0,1,{319,239},{319,239},{319,239},{4,4},BLUE, 10, 2, 0, 0};*/

void collision_detect2(void)
{
	if(Pitcher1_ball.ball_flag != 0 && Pitcher1_ball.cd_flag == 0)
	{
		if((Pitcher1_ball.pos[0] > Player.pos[0] + 20) && \
			(Pitcher1_ball.pos[0] + Pitcher1_ball.size[0] < Player.pos[0] + 60) )
		{
			if((Pitcher1_ball.pos[1] + Pitcher1_ball.size[1]  >= Player.pos[1]))
			{
				Pitcher1_ball.move_flag = 1;
				Player.move_flag = 1;

				Player.timer = 0;
				Pitcher1_ball.timer = 0;

				Pitcher1_ball.cd_flag = 1;
				Player.cd_flag = 1;
			}
		}
	}

	//Pitcher2
	/*	if(Pitcher2_ball.ball_flag != 0 && Pitcher2_ball.cd_flag == 0)
	{
	if((Pitcher2_ball.pos[0] > Player.pos[0] + 20) && \
	(Pitcher2_ball.pos[0] + Pitcher2_ball.size[0] < Player.pos[0] + 60) )
	{
	if((Pitcher2_ball.pos[1] + Pitcher2_ball.size[1]  >= Player.pos[1]))
	{
	Pitcher2_ball.move_flag = 1;
	Player.move_flag = 1;

	Player.timer = 0;
	Pitcher2_ball.timer = 0;

	Pitcher2_ball.cd_flag = 1;
	Player.cd_flag = 1;
	}
	}
	}*/

}

void contact(void)
{
	Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player_bat);
	Timer4_Delay(20);
	Lcd_Draw_BMP2(Player.pos_back[0], Player.pos_back[1], 70, 55, background); //61, 48
	Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
}


void Game_Start(void)
{
	Lcd_Clr_Screen(BLACK);
	Lcd_Draw_BMP(0, 0, background);
	Timer0_Repeat(10);
}

void Draw_Thing(void)
{
	if(game_strike == 0)  Lcd_Draw_BMP2(275, 155, 45, 20, background);
	if(game_strike == 1)  Lcd_Draw_Bar(278, 160, 291, 173, GREEN);
	if(game_strike == 2)  Lcd_Draw_Bar(299, 160, 312, 173, GREEN);
	if(game_strike == 3)
	{
		game_out++;
		game_strike == 0;
	}
	if(game_out == 1) Lcd_Draw_Bar(278, 189, 291, 202, RED);
	if(game_out == 2) Lcd_Draw_Bar(299, 189, 312, 202, RED);

	if(Player.move_flag != 0)
	{
		Lcd_Draw_BMP2(Player.pos_back[0], Player.pos_back[1], 35, 58, background); //25, 48
		Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
		Player.move_flag = 0;
	}
	if(Pitcher1.move_flag != 0)
	{
		Lcd_Draw_BMP2(Pitcher1.pos_back[0], Pitcher1.pos_back[1], 25, 55, background); //17, 46
		Lcd_Draw_BMP(Pitcher1.pos[0], Pitcher1.pos[1], pitcher1);
		Pitcher1.move_flag = 0;
	}
	if((Pitcher1_ball.pos[1] > 230))
	{
		game_strike++;
		if ((Pitcher1_ball.pos[1] > 239)) Pitcher1_ball.ball_flag = 0;
	}
	if(Pitcher1_ball.move_flag != 0)
	{
		Lcd_Draw_BMP2(Pitcher1_ball.pos_back[0], Pitcher1_ball.pos_back[1], 6, 6, background);
		Lcd_Draw_Bar(Pitcher1_ball.pos[0], Pitcher1_ball.pos[1], Pitcher1_ball.pos[0] + Pitcher1_ball.size[0], Pitcher1_ball.pos[1] + Pitcher1_ball.size[1], GREEN);
		Pitcher1_ball.move_flag = 0;
	}
	if(Player_ball.pos[0] < -4)
	{
		Player_ball.ball_flag = 0;
	}
	if(Player_ball.pos[1] < -4)
	{
		Player_ball.ball_flag = 0;
	}
	if(Player_ball.move_flag != 0)
	{
		Lcd_Draw_BMP2(Player_ball.pos_back[0], Player_ball.pos_back[1], 6, 6, background);
		Lcd_Draw_Bar(Player_ball.pos[0], Player_ball.pos[1], Player_ball.pos[0] + Player_ball.size[0], Player_ball.pos[1] + Player_ball.size[1], Player_ball.color);
		Player_ball.move_flag = 0;
	}
	/*
	if(Pitcher2.move_flag != 0)
	{
	Lcd_Draw_BMP2(Pitcher2.pos_back[0], Pitcher1.pos_back[1], 40, 55, background); //17, 46
	Lcd_Draw_BMP(Pitcher2.pos[0], Pitcher2.pos[1], pitcher2);
	Pitcher2.move_flag = 0;
	}
	if((Pitcher2_ball.pos[1] > 239 || Pitcher2_ball.pos[0]<-5))
	{
	Pitcher2_ball.ball_flag = 0;
	game_strike++;
	}
	if(Pitcher2_ball.move_flag != 0)
	{
	Lcd_Draw_BMP2(Pitcher2_ball.pos_back[0], Pitcher2_ball.pos_back[1], 6, 6, background);
	Lcd_Draw_Bar(Pitcher2_ball.pos[0], Pitcher2_ball.pos[1], Pitcher2_ball.pos[0] + Pitcher2_ball.size[0], Pitcher2_ball.pos[1] + Pitcher2_ball.size[1], Pitcher2_ball.color);
	Pitcher2_ball.move_flag = 0;
	}
	if(Player2_ball.pos[1] < -5)
	{
	Player2_ball.ball_flag = 0;
	}
	if(Player2_ball.move_flag != 0)
	{
	Lcd_Draw_BMP2(Player2_ball.pos_back[0], Player2_ball.pos_back[1], 6, 6, background);
	Lcd_Draw_Bar(Player2_ball.pos[0], Player2_ball.pos[1], Player2_ball.pos[0] + Player2_ball.size[0], Player2_ball.pos[1] + Player2_ball.size[1], Player2_ball.color);
	Player2_ball.move_flag = 0;
	}

	*/

}

void Move_Player(void)
{
	int key = 0;
	Player.timer++;

	key = Key_Get_Pressed();

	if(key == 2 && Player.pos_back[0]>40)
	{
		Player.timer = 0;
		Player.pos_back[0] = Player.pos[0];
		Player.pos[0] = Player.pos_back[0] - Player.move_step;
		Player.move_flag = 1;
	}
	if(key == 4 && Player.pos_back[0]<136)
	{
		Player.timer = 0;
		Player.pos_back[0] = Player.pos[0];
		Player.pos[0] = Player.pos_back[0] + Player.move_step;
		Player.move_flag = 1;
	}
	if(key == 1 && Player.pos_back[1]>152)
	{
		Player.timer = 0;
		Player.pos_back[1] = Player.pos[1];
		Player.pos[1] = Player.pos_back[1] - Player.move_step;
		Player.move_flag = 1;
	}
	if(key == 3 && Player.pos_back[1]<165)
	{
		Player.timer = 0;
		Player.pos_back[1] = Player.pos[1];
		Player.pos[1] = Player.pos_back[1] + Player.move_step;
		Player.move_flag = 1;
	}
	if(key == 5 && Player.cd_flag == 1) //일반치기
	{
		contact();
		//if (Pitcher1_ball.cd_flag == 1)
		//	{
		Player.cd_flag = 0;
		Pitcher1_ball.cd_flag = 0;
		Pitcher1_ball.ball_flag = 0;
		Player_ball.ball_flag = 1;
		/*			}
		else if (Pitcher2_ball.cd_flag == 1)
		{
		Player.cd_flag = 0;
		Pitcher2_ball.cd_flag = 0;
		Pitcher2_ball.ball_flag = 0;
		Player2_ball.ball_flag = 1;
		}*/

	}

	if(key == 6 && Player.cd_flag == 1) // 당겨치기
	{
		contact();
		//					if (Pitcher1_ball.cd_flag == 1)
		//				{
		Player.cd_flag = 0;
		Pitcher1_ball.cd_flag = 0;
		Pitcher1_ball.ball_flag = 0;
		Player_ball.ball_flag = 2;
		/*			}
		else if (Pitcher2_ball.cd_flag == 1)
		{
		Player.cd_flag = 0;
		Pitcher2_ball.cd_flag = 0;
		Pitcher2_ball.ball_flag = 0;
		Player2_ball.ball_flag = 2;
		}*/
	}

	if(key == 7 && Player.cd_flag == 1) // 밀어치기
	{
		contact();
		//			if (Pitcher1_ball.cd_flag == 1)
		//			{
		Player.cd_flag = 0;
		Pitcher1_ball.cd_flag = 0;
		Pitcher1_ball.ball_flag = 0;
		Player_ball.ball_flag = 3;
		/*			}
		else if (Pitcher2_ball.cd_flag == 1)
		{
		Player.cd_flag = 0;
		Pitcher2_ball.cd_flag = 0;
		Pitcher2_ball.ball_flag = 0;
		Player2_ball.ball_flag = 3;
		}*/
	}

}

void Move_Pitcher1(void)
{
	Pitcher1.timer++;
	Pitcher1_ball.timer++;
	/*Pitcher2.timer++;
	Pitcher2_ball.timer++;*/

	if ((Pitcher1.timer >= Pitcher1.speed_step) && Pitcher1.pos[0]<180)
	{
		Pitcher1.timer = 0;
		Pitcher1.pos_back[0] = Pitcher1.pos[0];
		Pitcher1.pos[0] = Pitcher1.pos[0] + Pitcher1.move_step;
		Pitcher1.move_flag = 1;
	}
	if (Pitcher1.pos[0]>180)
	{
		Pitcher1.timer = 0;
		Pitcher1.pos_back[0] = Pitcher1.pos[0];
		Pitcher1.pos[0] = Pitcher1.pos_init[0];
		Pitcher1.move_flag = 1;
	}
	if(Pitcher1_ball.ball_flag == 0)
	{
		Pitcher1_ball.pos_init[0] = Pitcher1.pos[0];
		Pitcher1_ball.pos_init[1] = Pitcher1.pos[1];
		Pitcher1_ball.pos_back[0] = Pitcher1_ball.pos_init[0];
		Pitcher1_ball.pos_back[1] = Pitcher1_ball.pos_init[1];
		Pitcher1_ball.pos[0] = Pitcher1_ball.pos_init[0];
		Pitcher1_ball.pos[1] = Pitcher1_ball.pos_init[1];

		if (Pitcher1_ball.timer >= Pitcher1_ball.speed_step)
		{
			Pitcher1_ball.timer = 0;
			Pitcher1_ball.pos_back[1] = Pitcher1_ball.pos[1];
			Pitcher1_ball.ball_flag = 1;
		}
	}
	if (Pitcher1_ball.ball_flag == 1)
	{
		Pitcher1_ball.pos_back[1] = Pitcher1_ball.pos[1];
		Pitcher1_ball.pos[1] = Pitcher1_ball.pos[1] + Pitcher1_ball.move_step;
		Pitcher1_ball.move_flag = 1;
	}

	if(Player_ball.ball_flag == 0)
	{
		Player_ball.pos_init[0] = Pitcher1_ball.pos_back[0];
		Player_ball.pos_init[1] = Pitcher1_ball.pos_back[1];
		Player_ball.pos_back[0] = Player_ball.pos_init[0];
		Player_ball.pos_back[1] = Player_ball.pos_init[1];
		Player_ball.pos[0] = Player_ball.pos_init[0];
		Player_ball.pos[1] = Player_ball.pos_init[1];
	}
	if (Player_ball.ball_flag == 1)
	{
		Player_ball.pos_back[1] = Player_ball.pos[1];
		Player_ball.pos[1] = Player_ball.pos[1] - (2*Player_ball.move_step);
		Player_ball.move_flag = 1;
	}
	if (Player_ball.ball_flag == 2)
	{
		Player_ball.pos_back[1] = Player_ball.pos[1];
		Player_ball.pos_back[0] = Player_ball.pos[0];
		Player_ball.pos[0] = Player_ball.pos[0] - Player_ball.move_step;
		Player_ball.pos[1] = Player_ball.pos[1] - (3*Player_ball.move_step);
		Player_ball.move_flag = 1;
	}

	if (Player_ball.ball_flag == 3)
	{
		Player_ball.pos_back[1] = Player_ball.pos[1];
		Player_ball.pos_back[0] = Player_ball.pos[0];
		Player_ball.pos[0] = Player_ball.pos[0] + Player_ball.move_step;
		Player_ball.pos[1] = Player_ball.pos[1] - (2*Player_ball.move_step);
		Player_ball.move_flag = 1;
	}

	/*	// Pitcher2

	if ((Pitcher2.timer >= Pitcher2.speed_step) && Pitcher2.pos[0]>200)
	{
	Pitcher2.timer = 0;
	Pitcher2.pos_back[0] = Pitcher2.pos[0];
	Pitcher2.pos[0] = Pitcher2.pos[0] + Pitcher2.move_step;
	Pitcher2.move_flag = 1;
	}
	if (Pitcher2.pos[0]>300)
	{
	Pitcher2.timer = 0;
	Pitcher2.pos_back[0] = Pitcher2.pos[0];
	Pitcher2.pos[0] = Pitcher2.pos_init[0];
	Pitcher2.move_flag = 1;
	}
	if(Pitcher2_ball.ball_flag == 0)
	{
	Pitcher2_ball.pos_init[0] = Pitcher2.pos[0];
	Pitcher2_ball.pos_init[1] = Pitcher2.pos[1];
	Pitcher2_ball.pos_back[0] = Pitcher2_ball.pos_init[0];
	Pitcher2_ball.pos_back[1] = Pitcher2_ball.pos_init[1];
	Pitcher2_ball.pos[0] = Pitcher2_ball.pos_init[0];
	Pitcher2_ball.pos[1] = Pitcher2_ball.pos_init[1];

	if (Pitcher2_ball.timer >= Pitcher2_ball.speed_step)
	{
	Pitcher2_ball.timer = 0;
	Pitcher2_ball.pos_back[1] = Pitcher2_ball.pos[1];
	Pitcher2_ball.ball_flag = 1;
	}
	}
	if (Pitcher2_ball.ball_flag == 1)
	{
	Pitcher2_ball.pos_back[1] = Pitcher2_ball.pos[1];
	Pitcher2_ball.pos[0] = Pitcher2_ball.pos[0] - (2*Pitcher2_ball.move_step);
	Pitcher2_ball.pos[1] = Pitcher2_ball.pos[1] + Pitcher2_ball.move_step;
	Pitcher2_ball.move_flag = 1;
	}

	if(Player2_ball.ball_flag == 0)
	{
	Player2_ball.pos_init[0] = Pitcher2_ball.pos_back[0];
	Player2_ball.pos_init[1] = Pitcher2_ball.pos_back[1];
	Player2_ball.pos_back[0] = Player2_ball.pos_init[0];
	Player2_ball.pos_back[1] = Player2_ball.pos_init[1];
	Player2_ball.pos[0] = Player2_ball.pos_init[0];
	Player2_ball.pos[1] = Player2_ball.pos_init[1];
	}
	if (Player2_ball.ball_flag == 1)
	{
	Player2_ball.pos_back[1] = Player2_ball.pos[1];
	Player2_ball.pos[1] = Player2_ball.pos[1] - (2*Player2_ball.move_step);
	Player2_ball.move_flag = 1;
	}
	if (Player2_ball.ball_flag == 2)
	{
	Player2_ball.pos_back[1] = Player2_ball.pos[1];
	Player2_ball.pos_back[0] = Player2_ball.pos[0];
	Player2_ball.pos[0] = Player2_ball.pos[0] - Player2_ball.move_step;
	Player2_ball.pos[1] = Player2_ball.pos[1] - (2*Player2_ball.move_step);
	Player2_ball.move_flag = 1;
	}

	if (Player2_ball.ball_flag == 3)
	{
	Player2_ball.pos_back[1] = Player2_ball.pos[1];
	Player2_ball.pos_back[0] = Player2_ball.pos[0];
	Player2_ball.pos[0] = Player2_ball.pos[0] + Player2_ball.move_step;
	Player2_ball.pos[1] = Player2_ball.pos[1] - (2*Player2_ball.move_step);
	Player2_ball.move_flag = 1;
	}

	*/

}

void Move_Character(void)
{
	if(Timer0_Check_Expired())
	{
		Move_Player();
		Move_Pitcher1();
	}
};

void Game_lose(void)
{
	Lcd_Clr_Screen(BLACK);
	Lcd_Draw_BMP(0, 0, lose);
	Timer4_Delay(10000);
}

void Three_vs_one(void)
{
	Game_Start();
	Draw_Thing();

	for(;;)
	{
		collision_detect2();
		Move_Character();
		Draw_Thing();
		if (game_out == 3) break;
	}
	Game_lose();
	Three_vs_one();
}
