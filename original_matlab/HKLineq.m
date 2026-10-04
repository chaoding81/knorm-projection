%%********************************************************************
%% HKLineq: solving the following problem: 
%% 
%% min{ 1/2 norm(x-a,2)^2 : sum(abs(x)) <= c, abs(x) <=b}
%%
%% x = HKLineq(a,c,b);
%%
%%*****************************************************************

function [x,R]=HKLineq(a,c,b)

a_abs=abs(a);

x=zeros(size(a));

if min(b)<=0 || c<0
    disp(' ---b and c should be non-negative--- ');
    return;
end

if a_abs<=b
    if sum(a_abs)<=c
        x=a;
        R= 0;
        return;
    end
end

xtemp=min(a_abs,b);

if sum(xtemp)<c
    x=sign(a).*xtemp;
    R = 0;
    return;
end

[x,R]=HKLeq(a_abs,ones(size(a)),c,b);

x=sign(a).*x;
