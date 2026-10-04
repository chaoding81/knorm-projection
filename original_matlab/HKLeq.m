%%********************************************************************
%% HKLeq: solving the following problem: 
%% 
%% min{ 1/2 norm(x-a,2)^2 : sum(abs(x)) == c, abs(x) <=b}
%%
%% [x,beta] = HKLeq(a,c,b);
%% Based on paper:  K. Helgason, J. Kennington, and H. Lall, A polynomially bounded algorithm for a
%% singly constrained quadratic program, Mathematical Programming, 18 (1980), pp. 338–343.
%%*****************************************************************

function [x,R]=HKLeq(a,d,c,b)

n=length(a); x=zeros(size(a));

y=[a-d.*b;a]; y=sort(y);

L=sum(b); R=0;
if c>L || c<0
    disp(' ---No feasible solution exists--- ')
    return;
end
l=1; r=2*n; 

while r-l>1
    m=floor(0.5*(l+r));
    temp=(a-y(m))./d;
    temp=max(min(temp,b),0);
    C=sum(temp);
    if C==c
        lambda=y(m);
        break;
    end
    if C>c
        l=m; L=C;
    end
    if C<c
        r=m; R=C;
    end
    if r-l==1
       lambda=y(l)+(y(r)-y(l))*(c-L)/(R-L);
    end
end

t=a-b.*d; t1=(a-lambda)./d;

x(t>=lambda)=b(t>=lambda);
x(t<lambda & a>=lambda)=t1(t<lambda & a>=lambda);

u = max(a-lambda-d.*b,0);
v = max(lambda-a,0);
R1= d.*x-a+u-v+lambda;
R2= u.*(x-b);
R3= v.*x;
R4 = norm([R1,R2,R3],'fro');
R5 = abs(sum(x)-c);
R = norm([R4,R5]);
%  keyboard