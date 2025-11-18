/*
GRAMOFON 1
Implemetirati program za upravljanje maketom gramofona. Gramofon ima jedan ulaz i dva izlaza.
Ulaz:  
	Start sistema  
Izlazi:			   
	[P0_2] Prolazak nitne ispod induktivnog davaca
	[P0_3] Detektovan krug motora

Uredjaj moze da radi u dva moda:
	1) Brojanje nitni - Uredjaj se startuje i svaki put kad detektuje krug motora na displeju ispise broj
nitni na gramofonu kao i vreme za koje napravi pun krug.
	2) Pomeranje gramofona za odreden broj nitni - Uredjaju se posalje komanda da se pomeri za
odredjeni broj nitni. Na displeju ispisati vreme (stavio zastitu da to sme da bude max 60s) za koje se 
gramofon pomerao.
Komande koje mogu da se posalju serijskom komunikacijom su:
~ Start
~ Stop
~ Pomeraj za odredjen broj nitni
Na displeju ispisati u prvom redu status gramofona a u drugom odgovarajuce parametre. 


*/

#include "display.h"

unsigned char start;
unsigned char mod;

char status;
int brojac_prekida;
unsigned char n=0;
unsigned char tajmer=0;

unsigned char brojacZaTaster=0;
unsigned char trenutno_hardversko_stanje_P0_0=1;
unsigned char prethodno_hardversko_stanje_P0_0=1;
unsigned char trenutno_softversko_P0_0=1;

unsigned char trenutno_hardversko_stanje_P0_1=1;
unsigned char prethodno_hardversko_stanje_P0_1=1;
unsigned char trenutno_softversko_P0_1=1;

unsigned char trenutno_hardversko_stanje_P0_2=1;
unsigned char prethodno_hardversko_stanje_P0_2=1;
unsigned char trenutno_softversko_P0_2=1;

unsigned char trenutno_hardversko_stanje_P0_3=1;
unsigned char prethodno_hardversko_stanje_P0_3=1;
unsigned char trenutno_softversko_P0_3=1;

char *ok = "OK\r\n";
char *greska = "ERROR\r\n";

char *slanje;
unsigned char buffer[12];
char buffer_it = 0;

void interrupt_t1(void) interrupt 3 {
	TL1 = 0x48;
	TH1 = 0x48;
	if (++brojac_prekida == 4650) {
		tajmer += 1;	  			// svaki put kad tajmer izbroji 1s
		status = 1;
		brojac_prekida = 0;
	}
   //P0_0 taster  ' start / stop '
   trenutno_hardversko_stanje_P0_0=P0_0;
   if(trenutno_hardversko_stanje_P0_0 == prethodno_hardversko_stanje_P0_0){
		if(++brojacZaTaster == 5){
			trenutno_softversko_P0_0 = trenutno_hardversko_stanje_P0_0;
			brojacZaTaster=0;
		}
	}
	else{
	 	brojacZaTaster=0;
	}
	prethodno_hardversko_stanje_P0_0 = trenutno_hardversko_stanje_P0_0;

	//P0_1 taster	' mod1 / mod2 '
	trenutno_hardversko_stanje_P0_1=P0_1;
	if(trenutno_hardversko_stanje_P0_1 == prethodno_hardversko_stanje_P0_1){
		if(++brojacZaTaster == 5){
			trenutno_softversko_P0_1 = trenutno_hardversko_stanje_P0_1;
			brojacZaTaster=0;
		}
	}
	else{
	 	brojacZaTaster=0;
	}
	prethodno_hardversko_stanje_P0_1 = trenutno_hardversko_stanje_P0_1;

	//P0_2 taster	' detektovana nitna '
	trenutno_hardversko_stanje_P0_2=P0_2;
	if(trenutno_hardversko_stanje_P0_2 == prethodno_hardversko_stanje_P0_2){
		if(++brojacZaTaster == 5){
			trenutno_softversko_P0_2 = trenutno_hardversko_stanje_P0_2;
			brojacZaTaster=0;
		}
	}
	else{
	 	brojacZaTaster=0;
	}
	prethodno_hardversko_stanje_P0_2 = trenutno_hardversko_stanje_P0_2;

	//P0_3 taster	' pun krug motora '
	trenutno_hardversko_stanje_P0_3=P0_3;
	if(trenutno_hardversko_stanje_P0_3 == prethodno_hardversko_stanje_P0_3){
		if(++brojacZaTaster == 5){
			trenutno_softversko_P0_3 = trenutno_hardversko_stanje_P0_3;
			brojacZaTaster=0;
		}
	}
	else{
	 	brojacZaTaster=0;
	}
	prethodno_hardversko_stanje_P0_3 = trenutno_hardversko_stanje_P0_3;
}

char *num2str(int broj){
	unsigned int i=0;
	unsigned int j;
	unsigned int ostatak;
	unsigned int len=0;
	unsigned int lenstr=0;
	char str[8];
	char pom[8];
	while(broj!=0){
		ostatak=broj%10;
		broj=broj/10;
		pom[i]=ostatak+48;
		len++;
		i++;
	}
	pom[len]='\0';
	lenstr=len;
	j=len-1;
	for(i=0; i<lenstr; i++, j--){
		str[i]=pom[j];
	}
	str[lenstr]='\0';
	return str;
}

void parsiraj_poruku(){
	// (START)
	if(buffer[0]=='(' && buffer[1]=='S' && buffer[2]=='T' && buffer[3]=='A' && buffer[4]=='R'&& buffer[5]=='T' && buffer[6]==')') {
		start=1;
		slanje=ok;
		mod = 0;
	}
	// (STOP)
	else if(buffer[0]=='(' && buffer[1]=='S' && buffer[2]=='T' && buffer[3]=='O' && buffer[4]=='P' && buffer[6]==')') {
		start=0;
		slanje=ok;
		P2=0x00;
	}
	// nitna (N:n) **podrazumevam da je n jednocifreno
	else if(buffer[0]=='(' && buffer[1]=='N' && buffer[2]==':' && buffer[4]==')') {
		n=buffer[3]-48;
		if(n>=0){
			if(mod){
				slanje=ok;
			}
		}
		else{
			slanje=greska;
		}
	}
	else{
		slanje=greska;
	}

	SBUF=*slanje;
	buffer[0]='\0';
	buffer_it=0;
}

void serijski_prekid(void)interrupt 4 {
	if(RI){
		char prijem;
		RI = 0;	
		prijem = SBUF;

		if(prijem=='('){
		 	buffer_it=0;
		}

		buffer[buffer_it] = prijem;
		buffer_it=(buffer_it+1)%12;

		if(prijem==')'){
			parsiraj_poruku();
		}
	}
	if(TI){
	 	TI = 0;

		slanje++;
		if(*slanje != '\0'){
			SBUF=*slanje;
		}
	}
}

void main(void){
	unsigned char nitna = 0;   // MOD1
	unsigned char nitna2 = 0;  // MOD2
	unsigned char trenutno_stanje_P0_0=1;
	unsigned char prethodno_stanje_P0_0=1;
	unsigned char trenutno_stanje_P0_1=1;
	unsigned char prethodno_stanje_P0_1=1;
	unsigned char trenutno_stanje_P0_2=1;
	unsigned char prethodno_stanje_P0_2=1;
	unsigned char trenutno_stanje_P0_3=1;
	unsigned char prethodno_stanje_P0_3=1;

	initDisplay();

	start = 0;
	mod = 0;
	P2=0;

	TL1 = 0x48;
	TH1 = 0x48;
	TMOD = 0x20;
	TR1 = 1;
	ET1 = 1;

	PCON &= 0x80; 
	BRL = 253;
	SCON = 0x50;
	BDRCON |= 0x1C;

	ES=1;
	EA=1;
	
	status = 0;
	brojac_prekida = 0;

	while(1){
		// P0_0  START / STOP
		trenutno_stanje_P0_0=trenutno_softversko_P0_0;
		if (trenutno_stanje_P0_0 > prethodno_stanje_P0_0) {
			start=~start;
			if(start){
				brojac_prekida = 0;
				TL1 = 0x48;
				TH1 = 0x48;
				mod = 0;
				nitna = 0;
				nitna2 = 0;
				tajmer = 0;
				
				clearDisplay();
				writeLine("MOD 1");
			}
			else{
				clearDisplay();
				writeLine("STOP");
				
				mod = 0;
				P2 = 0;
			}
		} 
	
		// P0_1 MOD1 / MOD2
		trenutno_stanje_P0_1=trenutno_softversko_P0_1;
		if (trenutno_stanje_P0_1 > prethodno_stanje_P0_1) {
			P2=0;
			mod=~mod;
			nitna = 0;
			nitna2 = 0;
			tajmer = 0;
			if(mod){
				clearDisplay();
				writeLine("MOD 2");
			}
			else{
			    clearDisplay();
				writeLine("MOD 1");
			}
		}

		// P0_2 Detektovana nitna
		trenutno_stanje_P0_2=trenutno_softversko_P0_2;

		// P0_3 Pun krug
		trenutno_stanje_P0_3=trenutno_softversko_P0_3;

		if(start){
			switch(mod){
				// MOD 1
				case 0:
					if(status){
						P2=0xFF;
						if(trenutno_stanje_P0_2 > prethodno_stanje_P0_2){
							nitna+=1;
						}
						if(trenutno_stanje_P0_3 > prethodno_stanje_P0_3){
							//ispis posto je presao pun krug
							clearDisplay();
							writeLine("MOD 1");	
							newLine();
							//ako je proslo vise od 60s
							if(tajmer>60){
								writeLine("timeout");
							}
							else{
								writeLine("n:");
								writeLine(num2str(nitna));
								writeLine(" ");
								writeLine(num2str(tajmer));
								writeLine("s");
							}
							tajmer=0;
							nitna=0;
						}
					}
					break;
				// MOD 2
				case 0xFF:
					if(status){
						if(n!=0){
							if (trenutno_stanje_P0_2 > prethodno_stanje_P0_2){
								nitna2+=1;
							}
							if(nitna2==n){
								P2=0;	  		
								clearDisplay();
								writeLine("MOD 2");	
								newLine();
								if(tajmer>60){
									writeLine("timeout");
								}
								else{
									writeLine(num2str(tajmer));
									writeLine("s");
								}
								tajmer=0;
								nitna2=0;
								n=0;
							}
							else{
								P2=0xFF;
							}
						}
						else{
							P2=0x00;
						}
					}
					break;
				default:
					P2=0x00;
					break;
			}
		}

	prethodno_stanje_P0_0 = trenutno_stanje_P0_0;
	prethodno_stanje_P0_1 = trenutno_stanje_P0_1;
	prethodno_stanje_P0_2 = trenutno_stanje_P0_2;
	prethodno_stanje_P0_3 = trenutno_stanje_P0_3;
	}
}

