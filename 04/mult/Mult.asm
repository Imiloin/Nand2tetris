// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

// Put your code here.
@sum
M = 0   // sum = 0

@R0
D = M
@R1
D = D - M
@POSITIVE
D; JGT  // R0 > R1

// <= 0
@R0
D = M
@i
M = D
@R1
D = M
@num
M = D
@LOOP
0; JMP

// > 0
(POSITIVE)
@R0
D = M
@num
M = D
@R1
D = M
@i
M = D


(LOOP)
@i
D = M
@RES
D; JEQ

@i
M = D - 1   // i--
@num
D = M
@sum
M = D + M
@LOOP
0; JMP

(RES)
@sum
D = M
@R2
M = D

(END)
@END
0; JMP