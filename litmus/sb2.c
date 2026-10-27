// Hardware probe: SB with a configurable gap between the store and the load, and a random
// pre-delay so the two bodies actually overlap. Orders: 0 relaxed, 1 rel/acq, 2 seq_cst.
#include <stdatomic.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#define N 4000000
static _Atomic int *X, *Y; static int *R0, *R1; static _Atomic long cnt[2];
static int order, gap;
static inline void spin(int k){ for (volatile int j=0;j<k;j++); }
static void *t(void *a){ long me=(long)a, o=1-me; unsigned s = 12345u*(me+1);
  _Atomic int *A = me?Y:X, *B = me?X:Y; int *R = me?R1:R0;
  for(long i=0;i<N;i++){
    while(atomic_load_explicit(&cnt[o],memory_order_relaxed)<i);
    s = s*1103515245u+12345u; spin((s>>16)&15);           // random pre-delay 0..15
    if(order==0){ atomic_store_explicit(&A[i],1,memory_order_relaxed); spin(gap); R[i]=atomic_load_explicit(&B[i],memory_order_relaxed);}
    else if(order==1){ atomic_store_explicit(&A[i],1,memory_order_release); spin(gap); R[i]=atomic_load_explicit(&B[i],memory_order_acquire);}
    else { atomic_store(&A[i],1); spin(gap); R[i]=atomic_load(&B[i]); }
    atomic_store_explicit(&cnt[me],i+1,memory_order_relaxed);} return 0;}
int main(int c,char**v){ order=atoi(v[1]); gap=atoi(v[2]);
  X=calloc(N,4);Y=calloc(N,4);R0=calloc(N,4);R1=calloc(N,4);
  pthread_t a,b; pthread_create(&a,0,t,(void*)0);pthread_create(&b,0,t,(void*)1);pthread_join(a,0);pthread_join(b,0);
  long h[4]={0}; for(long i=0;i<N;i++) h[R0[i]*2+R1[i]]++;
  const char*nm[]={"relaxed","rel/acq","seq_cst"};
  printf("%-8s gap=%-4d SB(0,0)=%-7ld rate=%.2e  (1,1)=%ld\n", nm[order],gap,h[0],h[0]/(double)N,h[3]); }
