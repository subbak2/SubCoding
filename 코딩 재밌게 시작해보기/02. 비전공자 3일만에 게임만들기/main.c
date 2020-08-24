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


void Two_vs_one(void);

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




		Timer3_Buzzer_Beep(F2_,N8);
		Timer3_Buzzer_Beep(E2,N8);
		Timer3_Buzzer_Beep(F2,N8);
		Timer3_Buzzer_Beep(G2_,N8);
		Timer3_Buzzer_Beep(A2,N4);
		Timer3_Buzzer_Beep(A2,N8);
		Timer3_Buzzer_Beep(E2,N4);
		Timer3_Buzzer_Beep(A2,N4);
		Timer3_Buzzer_Beep(B2,N8);
		Timer3_Buzzer_Beep(B2,N2);

		Timer3_Buzzer_Beep(A2,N8);
		Timer3_Buzzer_Beep(G2_,N8);
		Timer3_Buzzer_Beep(A2,N8);
		Timer3_Buzzer_Beep(A2,N2);
		Timer3_Buzzer_Beep(G2_,N8);
		Timer3_Buzzer_Beep(A2,N8);
		Timer3_Buzzer_Beep(B2,N2);
		Timer3_Buzzer_Beep(B2,N8);
		Timer3_Buzzer_Beep(A2,N8);
		Timer3_Buzzer_Beep(G2_,N8);
		Timer3_Buzzer_Beep(F2_,N4);


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
	int player_homerun;
	int score_factor;
};

struct Score Jebal_init = {0, 0, 0, 0, 19, 0, 0, 0, 0};
struct Score Jebal;

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

struct Thing Player_init = {0,1,{43,192},{43,192},{43,192},{24,48},BLACK, 1, 3, 0, 0};
struct Thing Pitcher1_init = {0,1,{77,60},{77,60},{77,60},{16,45},BLACK, 15, 5, 0, 0};
struct Thing Pitcher1_ball_init = {0,1,{318,10},{318,10},{318,10},{6,6}, YELLOW, 45, 1, 0, 0};
struct Thing Player_ball_init = {0,1,{318,10},{318,10},{318,10},{6,6}, YELLOW, 28, 1, 0, 0};

struct Thing Pitcher2_init = {0,1,{220,60},{220,60},{220,60},{16,45},BLACK, 20, 3, 0, 0};
struct Thing Pitcher2_ball_init = {0,1,{318,10},{318,10},{318,10},{6,6}, YELLOW, 80, 1, 0, 0};
struct Thing Player_ball2_init = {0,1,{318,10},{318,10},{318,10},{6,6}, YELLOW, 35, 1, 0, 0};

struct Thing Player;
struct Thing Pitcher1;
struct Thing Pitcher1_ball;
struct Thing Player_ball;
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
	Lcd_Draw_BMP(0, 0, nsplash1);
	while(!Key_Get_Pressed());
	Timer4_Delay(500);
	Lcd_Draw_BMP(0, 0, nsplash2);
	while(!Key_Get_Pressed());
	Timer4_Delay(500);
	Lcd_Draw_BMP(0, 0, nsplash3);
	while(!Key_Get_Pressed());
	Timer4_Delay(500);
	Lcd_Draw_BMP(0, 0, nsplash4);
	while(!Key_Get_Pressed());
	Timer4_Delay(500);
	Lcd_Draw_BMP(0, 0, nsplash5);
	while(!Key_Get_Pressed());
	Timer4_Delay(500);
	Lcd_Draw_BMP(0, 0, nsplash6);
	while(!Key_Get_Pressed());
	Timer4_Delay(500);
	Lcd_Draw_BMP(0, 0, background);
	Timer0_Repeat(18);
}

void contact(void)
{
	Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player_bat);
	// Timer3_Buzzer_Beep(G2,N16);
	Timer4_Delay(50);
	Lcd_Draw_BMP2(Player.pos_back[0], Player.pos_back[1], 100, 60, background); //61, 48
	Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
	Jebal.game_score+=10;
	Jebal.pitcher1_curve_step +=2;
	if (Jebal.pitcher1_curve_step>=6) Jebal.pitcher1_curve_step = 0;
	if (Jebal.player_homerun<20) Jebal.player_homerun+=1;
}

void collision_detect2(void)
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


	if(Pitcher1_ball.ball_flag != 0 && Pitcher1_ball.cd_flag == 0)
	{

		if((Pitcher1_ball.pos[0] > Player.pos[0] + 25) && \
			(Pitcher1_ball.pos[0] + Pitcher1_ball.size[0] < Player.pos[0] + 60) )
			{
				if((Pitcher1_ball.pos[1] + Pitcher1_ball.size[1]  > Player.pos[1] ) && \
					(Pitcher1_ball.pos[1] + Pitcher1_ball.size[1]  < Player.pos[1] + 47))
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

	if(Pitcher2_ball.ball_flag != 0 && Pitcher2_ball.cd_flag == 0)
		{

			if((Pitcher2_ball.pos[0] > Player.pos[0] + 25) && \
				(Pitcher2_ball.pos[0] + Pitcher2_ball.size[0] < Player.pos[0] + 60) )
				{
					if((Pitcher2_ball.pos[1] + Pitcher2_ball.size[1]  > Player.pos[1] ) && \
						(Pitcher2_ball.pos[1] + Pitcher2_ball.size[1]  < Player.pos[1] + 50))
					{
						Pitcher2_ball.move_flag = 1;
						Player.move_flag = 1;

						Player.timer = 0;
						Pitcher2_ball.timer = 0;

						Pitcher2_ball.cd_flag = 1;
						Player.cd_flag = 1;
					}
				}
		}

}

void Draw_Thing(void)
{
	if(Player.move_flag != 0 || Pitcher1_ball.timer == 0 )
	{
		Lcd_Draw_BMP2(Player.pos_back[0], Player.pos_back[1], 50, 76, background); //25, 48
		Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
		Player.move_flag = 0;
	}
	if(Pitcher1.move_flag != 0)
	{
		Lcd_Draw_BMP2(Pitcher1.pos_back[0], Pitcher1.pos_back[1], 25, 55, background); //17, 46
		Lcd_Draw_BMP(Pitcher1.pos[0], Pitcher1.pos[1], pitcher1);
		Pitcher1.move_flag = 0;
	}
	if(Pitcher1_ball.pos[1] > 238)
	{

		Pitcher1_ball.ball_flag = 0;
		if (Jebal.timer > Jebal.speed_step)
		{
			Jebal.timer = 0;
			Jebal.game_strike++;

			if(Jebal.game_score >= 1000 && Jebal.game_score <= 1200)
							{
							Jebal.score_factor++;
							if (Jebal.score_factor >=3) Jebal.score_factor=0;
							Pitcher2.speed_step -= (15*Jebal.score_factor);
							}
			if(Jebal.game_score >= 2000 && Jebal.game_score <= 2200)
				{
				Jebal.score_factor++;
				if (Jebal.score_factor >=3) Jebal.score_factor=0;
				Pitcher2.speed_step -= (15*Jebal.score_factor);
				}
			if(Jebal.game_score >= 3000 && Jebal.game_score <= 3200)
							{
							Jebal.score_factor++;
							if (Jebal.score_factor >=3) Jebal.score_factor=0;
							Pitcher2.speed_step -= (15*Jebal.score_factor);
							}
			if(Jebal.game_score >= 4000 && Jebal.game_score <= 4200)
									{
									Jebal.score_factor++;
									if (Jebal.score_factor >=3) Jebal.score_factor=0;
									Pitcher2.speed_step -= (15*Jebal.score_factor);
									}
			if(Jebal.game_score >= 5000 && Jebal.game_score <= 5200)
												{
												Jebal.score_factor++;
												if (Jebal.score_factor >=3) Jebal.score_factor=0;
												Pitcher2.speed_step -= (15*Jebal.score_factor);
												}
			if(Jebal.game_strike == 1)  Lcd_Draw_Bar(276, 189, 289, 202, GREEN);
			if(Jebal.game_strike == 2)  Lcd_Draw_Bar(301, 189, 314, 202, GREEN);
			if(Jebal.game_strike == 3)
			{
				Jebal.game_out++;
				Jebal.game_strike = 0;
				Lcd_Draw_BMP2(275, 185, 45, 20, background);
			}
		}
	}

	if(Pitcher1_ball.move_flag != 0)
	{
		Lcd_Draw_BMP2(Pitcher1_ball.pos_back[0], Pitcher1_ball.pos_back[1], 6, 6, background);
		Lcd_Draw_BMP(Pitcher1_ball.pos[0], Pitcher1_ball.pos[1], ball);
		Pitcher1_ball.move_flag = 0;
	}

	if((Player_ball.pos[1] >110)&& (Player_ball.pos[0] < 7 || Player_ball.pos[0] > 292) && Player_ball.ball_flag !=0)
		{
			Lcd_Draw_BMP2(Player_ball.pos[0], Player_ball.pos[1], 15, 15, background);
			Player_ball.ball_flag = 0;
			Lcd_Draw_BMP2(Player_ball.pos_back[0], Player_ball.pos_back[1], 15, 15, background);
			Lcd_Draw_BMP2(Player_ball.pos[0], Player_ball.pos[1], 15, 15, background);
			Lcd_Printf(190,7,WHITE,BLACK,1,1,"파울!");
			if(Jebal.game_strike < 2) Jebal.game_strike++;
			Jebal.game_score-=10;
		}

	if(Player_ball.pos[1] < (140 + Jebal.pitcher1_curve_step) && Jebal.player_homerun < 10 && Player_ball.ball_flag !=0)
	{
		Lcd_Draw_BMP2(Player_ball.pos[0], Player_ball.pos[1], 15, 15, background);
		Player_ball.ball_flag = 0;
		Lcd_Draw_BMP2(Player_ball.pos_back[0], Player_ball.pos_back[1], 15, 15, background);
		Lcd_Draw_BMP2(Player_ball.pos[0], Player_ball.pos[1], 15, 15, background);
		Lcd_Printf(190,7,WHITE,BLACK,1,1,"1루타");
	}

	if(Player_ball.pos[0] < 78 && Player_ball.pos[0] > 238 && Player_ball.pos[1] <90 &&\
			Jebal.player_homerun >= 10  && Jebal.player_homerun < 20)
	{
		Lcd_Draw_BMP2(Player_ball.pos[0], Player_ball.pos[1], 6, 6, background);
		Player_ball.ball_flag = 0;
		Lcd_Printf(190,7,WHITE,BLACK,1,1,"2루타");
		Jebal.game_score+=20;
	}

	if(Player_ball.pos[1] <40 && Jebal.player_homerun >= 10 && Jebal.player_homerun <= 20 && Jebal.player_homerun%3 != 0 && Player_ball.ball_flag !=4)
	{
		Lcd_Draw_BMP2(Player_ball.pos[0], Player_ball.pos[1], 6, 6, background);
		Player_ball.ball_flag = 0;
		Lcd_Printf(190,7,WHITE,BLACK,1,1,"2루타");
		Jebal.game_score+=20;
	}

	if(Player_ball.pos[1]  <20  && Jebal.player_homerun <= 20 && Player_ball.ball_flag !=0 && Player_ball.ball_flag !=4)
		{
			Lcd_Draw_BMP2(Player_ball.pos[0], Player_ball.pos[1], 6, 6, background);
			Player_ball.ball_flag = 0;
			Lcd_Printf(190,7,WHITE,BLACK,1,1,"3루타");
			Jebal.game_score+=40;
		}

	if(Player_ball.pos[1] < 7 && Player_ball.ball_flag == 4)
	{
			Lcd_Draw_BMP2(Player_ball.pos[0], Player_ball.pos[1], 6, 6, background);
			Player_ball.ball_flag = 0;
			Lcd_Printf(190,7,WHITE,BLACK,1,1,"홈런!");
			Jebal.game_score+=190;
			Jebal.player_homerun =0;
			Lcd_Draw_BMP(0, 0, homerun_effect);
			Timer3_Buzzer_Beep(C1,N16);
			Lcd_Draw_BMP(0, 0, homerun_effect2);
			Timer3_Buzzer_Beep(E1,N16);
			Lcd_Draw_BMP(0, 0, homerun_effect);
			Timer3_Buzzer_Beep(G1,N16);
			Lcd_Draw_BMP(0, 0, homerun_effect2);
			Timer3_Buzzer_Beep(C2,N8);
			Player_ball.move_flag = 0;
			Lcd_Draw_BMP(0, 0, homerun_effect);
			Timer3_Buzzer_Beep(G1,N16);
			Player_ball.move_flag = 1;
			Lcd_Draw_BMP(0, 0, homerun_effect2);
			Timer3_Buzzer_Beep(C2,N8);
			Lcd_Draw_BMP(0, 0, background);
			Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
	}
	if(Player_ball.move_flag != 0)
	{
		Lcd_Draw_BMP2(Player_ball.pos_back[0], Player_ball.pos_back[1], 6, 6, background);
		Lcd_Draw_BMP(Player_ball.pos[0], Player_ball.pos[1], ball);
		Player_ball.move_flag = 0;
	}

	// Player2
	if(Player.move_flag != 0 || Pitcher2_ball.timer == 0 )
		{
			Lcd_Draw_BMP2(Player.pos_back[0], Player.pos_back[1], 50, 76, background); //25, 48
			Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
			Player.move_flag = 0;
		}
		if(Pitcher2.move_flag != 0)
		{
			Lcd_Draw_BMP2(Pitcher2.pos_back[0], Pitcher2.pos_back[1], 40, 55, background); //17, 46
			Lcd_Draw_BMP(Pitcher2.pos[0], Pitcher2.pos[1], pitcher2);
			Pitcher2.move_flag = 0;
		}
		if(Pitcher2_ball.pos[1] > 238)
		{

			Pitcher2_ball.ball_flag = 0;
			if (Jebal.timer > Jebal.speed_step)
			{
				Jebal.timer = 0;
				Jebal.game_strike++;

				if(Jebal.game_strike == 1)  Lcd_Draw_Bar(276, 189, 289, 202, GREEN);
				if(Jebal.game_strike == 2)  Lcd_Draw_Bar(301, 189, 314, 202, GREEN);
				if(Jebal.game_strike == 3)
				{
					Jebal.game_out++;
					Jebal.game_strike = 0;
					Lcd_Draw_BMP2(275, 185, 45, 20, background);
				}
			}
		}

		if(Pitcher2_ball.move_flag != 0)
		{
			Lcd_Draw_BMP2(Pitcher2_ball.pos_back[0], Pitcher2_ball.pos_back[1], 6, 6, background);
			Lcd_Draw_BMP(Pitcher2_ball.pos[0], Pitcher2_ball.pos[1], ball);
			Pitcher2_ball.move_flag = 0;
		}

		if((Player_ball2.pos[1] >110)&& (Player_ball2.pos[0] < 7 || Player_ball2.pos[0] > 292) && Player_ball2.ball_flag !=0)
			{
				Lcd_Draw_BMP2(Player_ball2.pos[0], Player_ball2.pos[1], 15, 15, background);
				Player_ball2.ball_flag = 0;
				Lcd_Draw_BMP2(Player_ball2.pos_back[0], Player_ball2.pos_back[1], 15, 15, background);
				Lcd_Draw_BMP2(Player_ball2.pos[0], Player_ball2.pos[1], 15, 15, background);
				Lcd_Printf(190,7,WHITE,BLACK,1,1,"파울!");
				if(Jebal.game_strike < 2) Jebal.game_strike++;
				Jebal.game_score-=10;
			}

		if(Player_ball2.pos[1] < (140 + Jebal.pitcher1_curve_step) && Jebal.player_homerun < 10 && Player_ball2.ball_flag !=0)
		{
			Lcd_Draw_BMP2(Player_ball2.pos[0], Player_ball2.pos[1], 15, 15, background);
			Player_ball2.ball_flag = 0;
			Lcd_Draw_BMP2(Player_ball2.pos_back[0], Player_ball2.pos_back[1], 15, 15, background);
			Lcd_Draw_BMP2(Player_ball2.pos[0], Player_ball2.pos[1], 15, 15, background);
			Lcd_Printf(190,7,WHITE,BLACK,1,1,"1루타");
		}

		if(Player_ball2.pos[0] < 78 && Player_ball2.pos[0] > 238 && Player_ball2.pos[1] <90 &&\
				Jebal.player_homerun >= 10  && Jebal.player_homerun < 20)
		{
			Lcd_Draw_BMP2(Player_ball2.pos[0], Player_ball2.pos[1], 6, 6, background);
			Player_ball2.ball_flag = 0;
			Lcd_Printf(190,7,WHITE,BLACK,1,1,"2루타");
			Jebal.game_score+=20;
		}

		if(Player_ball2.pos[1] <40 && Jebal.player_homerun >= 10 && Jebal.player_homerun <= 20 && Jebal.player_homerun%3 != 0 && Player_ball2.ball_flag !=4)
		{
			Lcd_Draw_BMP2(Player_ball2.pos[0], Player_ball2.pos[1], 6, 6, background);
			Player_ball2.ball_flag = 0;
			Lcd_Printf(190,7,WHITE,BLACK,1,1,"2루타");
			Jebal.game_score+=20;
		}

		if(Player_ball2.pos[1]  <20  && Jebal.player_homerun <= 20 && Player_ball2.ball_flag !=0 && Player_ball2.ball_flag !=4)
			{
				Lcd_Draw_BMP2(Player_ball2.pos[0], Player_ball2.pos[1], 6, 6, background);
				Player_ball2.ball_flag = 0;
				Lcd_Printf(190,7,WHITE,BLACK,1,1,"3루타");
				Jebal.game_score+=40;
			}

		if(Player_ball2.pos[1] < 7 && Player_ball2.ball_flag == 4)
		{
				Lcd_Draw_BMP2(Player_ball2.pos[0], Player_ball2.pos[1], 6, 6, background);
				Player_ball2.ball_flag = 0;
				Lcd_Printf(190,7,WHITE,BLACK,1,1,"홈런!");
				Jebal.game_score+=190;
				Jebal.player_homerun =0;
				Lcd_Draw_BMP(0, 0, homerun_effect);
				Timer3_Buzzer_Beep(C1,N16);
				Lcd_Draw_BMP(0, 0, homerun_effect2);
				Timer3_Buzzer_Beep(E1,N16);
				Lcd_Draw_BMP(0, 0, homerun_effect);
				Timer3_Buzzer_Beep(G1,N16);
				Lcd_Draw_BMP(0, 0, homerun_effect2);
				Timer3_Buzzer_Beep(C2,N8);
				Player_ball2.move_flag = 0;
				Lcd_Draw_BMP(0, 0, homerun_effect);
				Timer3_Buzzer_Beep(G1,N16);
				Player_ball2.move_flag = 1;
				Lcd_Draw_BMP(0, 0, homerun_effect2);
				Timer3_Buzzer_Beep(C2,N8);
				Lcd_Draw_BMP(0, 0, background);
				Lcd_Draw_BMP(Player.pos[0], Player.pos[1], player);
		}
		if(Player_ball2.move_flag != 0)
		{
			Lcd_Draw_BMP2(Player_ball2.pos_back[0], Player_ball2.pos_back[1], 6, 6, background);
			Lcd_Draw_BMP(Player_ball2.pos[0], Player_ball2.pos[1], ball);
			Player_ball2.move_flag = 0;
		}


}

void Move_Player(void)
{
	int key = 0;
	Player.timer++;

	key = Key_Get_Pressed();

	if(key == 2 && Player.pos_back[0]>50)
	{
		Player.timer = 0;
		Player.pos_back[0] = Player.pos[0];
		Player.pos[0] = Player.pos_back[0] - Player.move_step;
		Player.move_flag = 1;
		if (++Jebal.pitcher1_curve_step >=6) Jebal.pitcher1_curve_step = 0;
	}
	if(key == 4 && Player.pos_back[0]<175)
	{
		Player.timer = 0;
		Player.pos_back[0] = Player.pos[0];
		Player.pos[0] = Player.pos_back[0] + Player.move_step;
		Player.move_flag = 1;
		if (++Jebal.pitcher1_curve_step >=6) Jebal.pitcher1_curve_step = 0;
	}
	if(key == 1 && Player.pos_back[1]>180)
	{
		Player.timer = 0;
		Player.pos_back[1] = Player.pos[1];
		Player.pos[1] = Player.pos_back[1] - Player.move_step;
		Player.move_flag = 1;
	}
	if(key == 3 && Player.pos_back[1]<192)
	{
		Player.timer = 0;
		Player.pos_back[1] = Player.pos[1];
		Player.pos[1] = Player.pos_back[1] + Player.move_step;
		Player.move_flag = 1;
	}
	if(key == 5 && Player.cd_flag == 1) //일반치기
	{
		contact();
		Player.cd_flag = 0;
		if (Pitcher1_ball.cd_flag == 1)
		{
			Pitcher1_ball.cd_flag = 0;
			Pitcher1_ball.ball_flag = 0;
			Player_ball.ball_flag = 1;
		}
		if (Pitcher2_ball.cd_flag == 1)
		{
			Pitcher2_ball.cd_flag = 0;
			Pitcher2_ball.ball_flag = 0;
			Player_ball2.ball_flag = 1;
		}
		Jebal.player_curve_step+=1;
		if (Jebal.player_curve_step >= 4) Jebal.player_curve_step = 0;
		if (Player.pos[0]>=115 && Player.pos[0]>=150)
		{
			if (Jebal.player_homerun<=15) Jebal.player_homerun+=5;
			else Jebal.player_homerun=20;
			}
	}

	if(key == 6 && Player.cd_flag == 1) // 당겨치기
	{
		contact();
		Player.cd_flag = 0;
		if (Pitcher1_ball.cd_flag == 1)
		{
			Pitcher1_ball.cd_flag = 0;
			Pitcher1_ball.ball_flag = 0;
			Player_ball.ball_flag = 2;
		}
		if (Pitcher2_ball.cd_flag == 1)
		{
			Pitcher2_ball.cd_flag = 0;
			Pitcher2_ball.ball_flag = 0;
			Player_ball2.ball_flag = 2;
		}
		Jebal.player_curve_step+=2;
		if (Jebal.player_curve_step >= 4) Jebal.player_curve_step = 0;
		if (Player.pos[0]<=115)
			{
			if (Jebal.player_homerun<=15) Jebal.player_homerun+=5;
			else Jebal.player_homerun=20;
			}
	}

	if(key == 7 && Player.cd_flag == 1) // 밀어치기
	{
		contact();
		Player.cd_flag = 0;
		if (Pitcher1_ball.cd_flag == 1)
		{
			Pitcher1_ball.cd_flag = 0;
			Pitcher1_ball.ball_flag = 0;
			Player_ball.ball_flag = 3;
		}
		if (Pitcher2_ball.cd_flag == 1)
		{
			Pitcher2_ball.cd_flag = 0;
			Pitcher2_ball.ball_flag = 0;
			Player_ball2.ball_flag = 3;

		}
		Jebal.player_curve_step+=1;
		if (Jebal.player_curve_step >= 5) Jebal.player_curve_step = 0;
		if (Player.pos[0]>150) {
			if (Jebal.player_homerun<=15) Jebal.player_homerun+=5;
			else Jebal.player_homerun=20;
			}
	}

	if(key == 8 && Player.cd_flag == 1 && Jebal.player_homerun == 20) // 홈런
		{
			contact();
			Player.cd_flag = 0;
			if (Pitcher1_ball.cd_flag == 1)
			{
				Pitcher1_ball.cd_flag = 0;
				Pitcher1_ball.ball_flag = 0;
				Player_ball.ball_flag = 4;
			}
			if (Pitcher2_ball.cd_flag == 1)
			{
				Pitcher2_ball.cd_flag = 0;
				Pitcher2_ball.ball_flag = 0;
				Player_ball2.ball_flag = 4;
			}
			Jebal.player_curve_step+=2;
			if (Jebal.player_curve_step >= 5) Jebal.player_curve_step = 0;
		}

}

void Move_Pitcher1(void)
{
	Pitcher1.timer++;
	Pitcher1_ball.timer++;

	if ((Pitcher1.timer >= Pitcher1.speed_step) && Pitcher1.pos[0]<120)
	{
		Pitcher1.timer = 0;
		Pitcher1.pos_back[0] = Pitcher1.pos[0];
		Pitcher1.pos[0] = Pitcher1.pos[0] + Pitcher1.move_step;
		Pitcher1.move_flag = 1;
	}
	if (Pitcher1.pos[0]>=120)
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
		Pitcher1_ball.pos_back[0] = Pitcher1_ball.pos[0];
		Pitcher1_ball.pos_back[1] = Pitcher1_ball.pos[1];
		if (Jebal.game_score%3 !=0)
		{
			if (Pitcher1_ball.pos_back[0] < 120 && Pitcher1_ball.pos_back[0] > 90)
			{
				Pitcher1_ball.pos[0] = Pitcher1_ball.pos[0] + ((Jebal.pitcher1_curve_step+4)%5-2)*Pitcher1_ball.move_step;
			}
			else Pitcher1_ball.pos[0] = Pitcher1_ball.pos[0] + Pitcher1_ball.move_step;
			if (Pitcher1_ball.pos_back[1] > 160)
			{
				Pitcher1_ball.pos[1] = Pitcher1_ball.pos[1] + (2*Pitcher1_ball.move_step);
			}
			else Pitcher1_ball.pos[1] = Pitcher1_ball.pos[1] + Pitcher1_ball.move_step;
		}
		else
			{
			Pitcher1_ball.pos[0] = Pitcher1_ball.pos[0] + Pitcher1_ball.move_step;
			Pitcher1_ball.pos[1] = Pitcher1_ball.pos[1] + (2*Pitcher1_ball.move_step);
			}
		Pitcher1_ball.move_flag = 1;
	}

	if(Player_ball.ball_flag == 0)
	{
		Player_ball.pos_init[0] = (Player.pos[0]+55);
		Player_ball.pos_init[1] = (Player.pos[1]+15);
		Player_ball.pos_back[0] = Player_ball.pos_init[0];
		Player_ball.pos_back[1] = Player_ball.pos_init[1];
		Player_ball.pos[0] = Player_ball.pos_init[0];
		Player_ball.pos[1] = Player_ball.pos_init[1];
	}
	if (Player_ball.ball_flag == 1)
	{
		Player_ball.pos_back[1] = Player_ball.pos[1];
		Player_ball.pos_back[0] = Player_ball.pos[0];
		Player_ball.pos[0] = Player_ball.pos[0] + ((Jebal.player_curve_step%3)-1)*Player_ball.move_step;
		Player_ball.pos[1] = Player_ball.pos[1] - (3*Player_ball.move_step);
		Player_ball.move_flag = 1;
	}
	if (Player_ball.ball_flag == 2)
	{
		Player_ball.pos_back[1] = Player_ball.pos[1];
		Player_ball.pos_back[0] = Player_ball.pos[0];
		Player_ball.pos[0] = Player_ball.pos[0] - ((2+(Jebal.player_curve_step%4))*Player_ball.move_step);
		Player_ball.pos[1] = Player_ball.pos[1] - (3*Player_ball.move_step);
		Player_ball.move_flag = 1;
	}

	if (Player_ball.ball_flag == 3)
	{
		Player_ball.pos_back[1] = Player_ball.pos[1];
		Player_ball.pos_back[0] = Player_ball.pos[0];
		Player_ball.pos[0] = Player_ball.pos[0] + ((1+(Jebal.player_curve_step%4))*Player_ball.move_step);
		Player_ball.pos[1] = Player_ball.pos[1] - (2*Player_ball.move_step);
		Player_ball.move_flag = 1;
	}
	if (Player_ball.ball_flag == 4)
		{
			Player_ball.pos_back[1] = Player_ball.pos[1];
			Player_ball.pos_back[0] = Player_ball.pos[0];
			Player_ball.pos[0] = Player_ball.pos[0] + ((Jebal.pitcher1_curve_step%5)-2)*Player_ball.move_step;
			Player_ball.pos[1] = Player_ball.pos[1] - (4*Player_ball.move_step);
			Player_ball.move_flag = 1;
		}

//Player2
	Pitcher2.timer++;
		Pitcher2_ball.timer++;

		if ((Pitcher2.timer >= Pitcher2.speed_step) && Pitcher2.pos[0]>185)
		{
			Pitcher2.timer = 0;
			Pitcher2.pos_back[0] = Pitcher2.pos[0];
			Pitcher2.pos[0] = Pitcher2.pos[0] - Pitcher2.move_step;
			Pitcher2.move_flag = 1;
		}
		if (Pitcher2.pos[0]<=185)
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
			Pitcher2_ball.pos_back[0] = Pitcher2_ball.pos[0];
			Pitcher2_ball.pos_back[1] = Pitcher2_ball.pos[1];
			if (Jebal.game_score%6 !=0)
			{
				if (Pitcher2_ball.pos[0] > 140 && Pitcher2_ball.pos[0] <= 220)
				{
					Pitcher2_ball.pos[0] = Pitcher2_ball.pos[0] - ((Jebal.pitcher1_curve_step+4)%5)*Pitcher2_ball.move_step;
				}
				if (Pitcher2_ball.pos[1] > 170)
				{
					if (Pitcher2_ball.pos[0] >240) Pitcher2_ball.pos[0] = Pitcher2_ball.pos[0] - Pitcher2_ball.move_step;
					else if (Pitcher2_ball.pos[0] <=100)  Pitcher2_ball.pos[0] = Pitcher2_ball.pos[0] + Pitcher2_ball.move_step;
					Pitcher2_ball.pos[1] = Pitcher2_ball.pos[1] + Pitcher2_ball.move_step;
				}
				else Pitcher2_ball.pos[1] = Pitcher2_ball.pos[1] + ((Jebal.pitcher1_curve_step+4)%5+1)*Pitcher2_ball.move_step;
			}
			else
				{
				if (Pitcher2_ball.pos[0] >240) Pitcher2_ball.pos[0] = Pitcher2_ball.pos[0] - Pitcher2_ball.move_step;
				else if (Pitcher2_ball.pos[0] <=100)  Pitcher2_ball.pos[0] = Pitcher2_ball.pos[0] + Pitcher2_ball.move_step;
				Pitcher2_ball.pos[1] = Pitcher2_ball.pos[1] + (2*Pitcher2_ball.move_step);
				}
			Pitcher2_ball.move_flag = 1;
		}

		if(Player_ball2.ball_flag == 0)
		{
			Player_ball2.pos_init[0] = (Player.pos[0]+55);
			Player_ball2.pos_init[1] = (Player.pos[1]+15);
			Player_ball2.pos_back[0] = Player_ball2.pos_init[0];
			Player_ball2.pos_back[1] = Player_ball2.pos_init[1];
			Player_ball2.pos[0] = Player_ball2.pos_init[0];
			Player_ball2.pos[1] = Player_ball2.pos_init[1];
		}
		if (Player_ball2.ball_flag == 1)
		{
			Player_ball2.pos_back[1] = Player_ball2.pos[1];
			Player_ball2.pos_back[0] = Player_ball2.pos[0];
			Player_ball2.pos[0] = Player_ball2.pos[0] + ((Jebal.player_curve_step%3)-1)*Player_ball2.move_step;
			Player_ball2.pos[1] = Player_ball2.pos[1] - (3*Player_ball2.move_step);
			Player_ball2.move_flag = 1;
		}
		if (Player_ball2.ball_flag == 2)
		{
			Player_ball2.pos_back[1] = Player_ball2.pos[1];
			Player_ball2.pos_back[0] = Player_ball2.pos[0];
			Player_ball2.pos[0] = Player_ball2.pos[0] - ((2+(Jebal.player_curve_step%4))*Player_ball2.move_step);
			Player_ball2.pos[1] = Player_ball2.pos[1] - (3*Player_ball2.move_step);
			Player_ball2.move_flag = 1;
		}

		if (Player_ball2.ball_flag == 3)
		{
			Player_ball2.pos_back[1] = Player_ball2.pos[1];
			Player_ball2.pos_back[0] = Player_ball2.pos[0];
			Player_ball2.pos[0] = Player_ball2.pos[0] + ((1+(Jebal.player_curve_step%4))*Player_ball2.move_step);
			Player_ball2.pos[1] = Player_ball2.pos[1] - (2*Player_ball2.move_step);
			Player_ball2.move_flag = 1;
		}
		if (Player_ball2.ball_flag == 4)
			{
				Player_ball2.pos_back[1] = Player_ball2.pos[1];
				Player_ball2.pos_back[0] = Player_ball2.pos[0];
				Player_ball2.pos[0] = Player_ball2.pos[0] + ((Jebal.pitcher1_curve_step%5)-2)*Player_ball2.move_step;
				Player_ball2.pos[1] = Player_ball2.pos[1] - (4*Player_ball2.move_step);
				Player_ball2.move_flag = 1;
			}


}

void Move_Character(void)
{
	if(Timer0_Check_Expired())
	{
		Jebal.timer++;
		Move_Player();
		Move_Pitcher1();
	}
};

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

#endif
