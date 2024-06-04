; procedure for A * B
define A 6
define B 4
  ldi r1 0 ; accumulator
  ldi r2 A ; A = 6
  ldi r3 B ; B = 4
  ldi r4 1 ; mask = 0x01
.loop
  cmp r3 r0
  brh = .done       ; exit loop if B is 0
  and r5 r3 r4      ; r5 = B & mask
  cmp r5 r0
  brh ne .add       ; add A to acc if LSB is set
  jmp .nadd         ; else don't
.add
  add r1, r1, r2    ; acc = acc + A ; comma separated operands test
.nadd
  lsh r2 r2         ; A = A << 1
  rsh r3 r3         ; B = B >> 1
  jmp .loop
done:               ; different format label test
  str r1 r0 0       ; store result in memory at index 0
  hlt               ; halt
