#include <Servo.h>

Servo s1;  
Servo s2;  
Servo s3;
Servo s4;  
Servo s5;  
Servo s6;  



void setup() {
  s1.attach(9); 
  s2.attach(8);  
  s3.attach(10);  
  s4.attach(11);  
  s5.attach(7);  
  s6.attach(6);  

}

void loop() {
  // Move de 0 a 180 graus
  for (int angulo = 0; angulo <= 180; angulo += 1) {
    s1.write(angulo);
    s2.write(angulo);
    s3.write(angulo);
    s4.write(angulo);
    s5.write(angulo);
    s6.write(angulo);

    delay(5); // Espera 15ms para o motor alcançar a posição
  }

  // Move de 180 a 0 graus
  for (int angulo = 180; angulo >= 0; angulo -= 1) {
    s1.write(angulo);
    s2.write(angulo);
    s3.write(angulo);
    s4.write(angulo);
    s5.write(angulo);
    s6.write(angulo);
    
    delay(10);
  }
}
