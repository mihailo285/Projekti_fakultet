#include "display.h"
#include <intrins.h>

void initP1P3(void)
{
	// inicijalizacija portova koji se koriste za lcd
	P1 = 0xE0;
	P3 = 0xF9;
}
void wait1s(void)
{
	// posle inicijalizacije portova se ceka 1 sekund
	unsigned char i;

	TMOD = (TMOD&0xF0) | 0x01;
	for(i = 0; i < 200; i++)
	{
		TH0 = 0xEE;
		TL0 = 0x00;				  //4562
		TR0 = 1;
		while(!TF0)
		{
		}
		TF0 = 0;
	}
	
}
void wait50micro(void)
{
		
	  TH0 = 0xFF;	   //65536 //2 / 
	  TL0 = 0xD2;
	  TR0 = 1;
	  while(!TF0)
	  {
	  }
	  TF0 = 0;
}
void wait2ms(void)
{

	TH0 = 0xF8; //isto kao prethodno samo brojis 2ms
	TL0 = 0xCD;
	TR0 = 1;
	while (!TF0)
	{
	}
	TF0 = 0;
}
void initDisplay(void)
{
	initP1P3();

	wait1s();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 0;
	LCD_EN = 0;

	wait50micro();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 1;
	LCD_D4 = 0;
	LCD_EN = 0;

	_nop_();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 1;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 0;
	LCD_EN = 0;

	wait50micro();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 0;
	LCD_EN = 0;

	_nop_();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 1;
	LCD_D6 = 1;
	LCD_D5 = 1;
	LCD_D4 = 1;
	LCD_EN = 0;

	wait50micro();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 0;
	LCD_EN = 0;

	_nop_();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 1;
	LCD_EN = 0;

	wait2ms();
	wait2ms();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 0;
	LCD_EN = 0;

	_nop_();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 1;
	LCD_D5 = 1;
	LCD_D4 = 0;
	LCD_EN = 0;

	wait50micro();

	wait2ms();
	LCD_BL = 1;



 
}
void clearDisplay(void)
{
	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 0;
	LCD_EN = 0;

	_nop_();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 1;
	LCD_EN = 0;

	wait2ms();
	wait2ms();


}
void newLine(void)
{
	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 1;
	LCD_D6 = 1;
	LCD_D5 = 0;
	LCD_D4 = 0;
	LCD_EN = 0;

	_nop_();

	LCD_RS = 0;
	LCD_EN = 1;
	LCD_D7 = 0;
	LCD_D6 = 0;
	LCD_D5 = 0;
	LCD_D4 = 0;
	LCD_EN = 0;

	wait2ms();
	wait2ms();
}
bit getbit(unsigned char n, unsigned char k)
{
	unsigned char mask = 1 << k;
	unsigned char masked_n = n & mask;
	bit thebit = masked_n >> k;
	return thebit;
}
void writeChar(unsigned char karakter)
{
	LCD_RS = 1;
	LCD_EN = 1;
	LCD_D7 = getbit(karakter, 7);
	LCD_D6 = getbit(karakter, 6);
	LCD_D5 = getbit(karakter, 5);
	LCD_D4 = getbit(karakter, 4);
	LCD_EN = 0;

	_nop_();

	LCD_EN = 1;
	LCD_D7 = getbit(karakter, 3);
	LCD_D6 = getbit(karakter, 2);
	LCD_D5 = getbit(karakter, 1);
	LCD_D4 = getbit(karakter, 0);
	LCD_EN = 0;

	wait50micro();
}
void writeLine(unsigned char *poruka)
{
	unsigned char n = 0;
	while(poruka[n] != '\0')
	{
		writeChar(poruka[n]);
		n++;
	}	
}

// u prvom redu start ili stop
// u drugom redu mod 1 2 3 ili 4

	 