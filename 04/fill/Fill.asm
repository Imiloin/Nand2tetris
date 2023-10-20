// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.
(OUTERLOOP)
@KBD
D = M
@PRESS
D; JNE

@key
D = M
M = 0
@OUTERLOOP
D; JEQ
@FILL
0; JMP

(PRESS)
@key
D = M
M = -1
@OUTERLOOP
D; JNE

(FILL)
@SCREEN
D = A
@addr
M = D   // addr = SCREEN[0]
@32
D = A
@i
M = D

(LOOPB)
@16
D = A
@j
M = D

(LOOPS) // 16 - loop
@key
D = M
@addr
A = M
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
A = A + 1
M = D
@16
D = A
@addr
M = D + M
@j
MD = M - 1
@LOOPS
D; JNE  // j != 0

@i
MD = M - 1
@LOOPB
D; JNE  // i != 0

@OUTERLOOP
0; JMP