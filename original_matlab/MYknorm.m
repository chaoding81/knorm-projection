function MY=MYknorm(Y,lambda,k)

MY=zeros(size(Y));
[PY,R] = Projdualk(Y,lambda,k);
MY=Y-PY;

fprintf(' ******** Error of Projdualk = %3.2e ********* \n',R)
