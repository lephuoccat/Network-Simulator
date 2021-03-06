X = csvread('output1.csv');
figure(1)
plot(X(:,1),X(:,2))
xlabel('time')
ylabel('window size')
ylim([0,16])
xlim([0,100])

figure(2)
plot(X(:,1),X(:,3))
xlabel('time')
ylabel('packet delay')
xlim([0,100])

figure(3)
plot(X(:,1),X(:,4))
xlabel('time')
ylabel('flow rate (kB/s)')
xlim([0,100])

figure(4)
plot(X(:,1),X(:,6),X(:,1),X(:,7))
legend('L1','L2')
xlabel('time')
ylabel('Link Rate (kB/s)')
xlim([0,100])

figure(5)
plot(X(:,1),X(:,11),X(:,1),X(:,12),X(:,1),X(:,13),X(:,1),X(:,14),X(:,1),X(:,15),X(:,1),X(:,16))
xlabel('time')
ylabel('packet drop')
xlim([0,100])

figure(6)
plot(X(:,1),X(:,18)./1000,X(:,1),X(:,19)./1000)
xlabel('time')
ylabel('buffer occupancy (in kB)')
xlim([0,100])
ylim([-0.05,20])

figure(7)
plot(X(:,1),X(:,17)./1000,X(:,1),X(:,18)./1000,X(:,1),X(:,19)./1000,X(:,1),X(:,20)./1000,X(:,1),X(:,21)./1000,X(:,1),X(:,22)./1000)
legend('L0','L1','L2','L3','L4','L5')
xlabel('time')
ylabel('buffer occupancy (in kB)')
xlim([0,100])
ylim([-0.05,20])