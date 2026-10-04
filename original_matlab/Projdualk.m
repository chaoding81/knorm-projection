function [PX,R]=Projdualk(X,r,k)

PX = X;

[U,S,V]=svd(X,'econ'); 
s=diag(S);
N1=s(1); 
N2=norm(s,1);

if N1<=r
    if N2<=k*r
        R = 0;
        return;
    end
end

b=r*ones(size(s));

[Ps,R]=HKLineq(s,k*r,b);

D=sparse(diag(Ps));

PX=U*D*V';
