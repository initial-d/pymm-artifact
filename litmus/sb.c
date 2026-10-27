// Hardware control: store buffering with relaxed atomics on Apple Silicon.
#include <stdatomic.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#define N 2000000
static _Atomic int *X, *Y; static int *R0, *R1; static _Atomic long cnt[2];
static int mode; // 0 relaxed, 1 seq_cst
static void *t(void *a){ long me=(long)a, o=1-me;
  for(long i=0;i<N;i++){ while(atomic_load_explicit(&cnt[o],memory_order_relaxed)<i);
    if(mode==0){ if(me==0){atomic_store_explicit(&X[i],1,memory_order_relaxed);R0[i]=atomic_load_explicit(&Y[i],memory_order_relaxed);}
                 else    {atomic_store_explicit(&Y[i],1,memory_order_relaxed);R1[i]=atomic_load_explicit(&X[i],memory_order_relaxed);} }
    else       { if(me==0){atomic_store(&X[i],1);R0[i]=atomic_load(&Y[i]);} else {atomic_store(&Y[i],1);R1[i]=atomic_load(&X[i]);} }
    atomic_store_explicit(&cnt[me],i+1,memory_order_relaxed);} return 0;}
int main(int c,char**v){ mode=atoi(v[1]); X=calloc(N,4);Y=calloc(N,4);R0=calloc(N,4);R1=calloc(N,4);
  pthread_t a,b; pthread_create(&a,0,t,(void*)0);pthread_create(&b,0,t,(void*)1);pthread_join(a,0);pthread_join(b,0);
  long h[4]={0}; for(long i=0;i<N;i++) h[R0[i]*2+R1[i]]++;
  printf("C SB %s n=%d  (0,0)=%ld (0,1)=%ld (1,0)=%ld (1,1)=%ld\n", mode?"seq_cst":"relaxed",N,h[0],h[1],h[2],h[3]); }
