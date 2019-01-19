%% Instrument Connection

% Find a VISA-GPIB object.
obj1 = instrfind('Type', 'visa-gpib', 'RsrcName', 'GPIB0::11::INSTR', 'Tag', '');

% Create the VISA-GPIB object if it does not exist
% otherwise use the object that was found.
if isempty(obj1)
    obj1 = visa('KEYSIGHT', 'GPIB0::11::INSTR');
else
    fclose(obj1);
    obj1 = obj1(1);
end



% Find a VISA-GPIB object.
obj2 = instrfind('Type', 'visa-gpib', 'RsrcName', 'GPIB0::7::INSTR', 'Tag', '');

% Create the VISA-GPIB object if it does not exist
% otherwise use the object that was found.
if isempty(obj2)
    obj2 = visa('KEYSIGHT', 'GPIB0::7::INSTR');
else
    fclose(obj2);
    obj2 = obj2(1);
end

% Connect to instrument object, obj1.
fopen(obj2);
fprintf(obj2,':FREQ:FIX 5.011 GHz');
fprintf(obj2,':FREQ:STEP 100 MHZ');


% Find a VISA-GPIB object.
obj3 = instrfind('Type', 'visa-gpib', 'RsrcName', 'GPIB0::15::INSTR', 'Tag', '');

% Create the VISA-GPIB object if it does not exist
% otherwise use the object that was found.
if isempty(obj3)
    obj3 = visa('KEYSIGHT', 'GPIB0::15::INSTR');
else
    fclose(obj3);
    obj3 = obj3(1);
end

% Connect to instrument object, obj1.
fopen(obj3);
fprintf(obj3,':FREQ:FIX 5 GHz');
fprintf(obj3,':FREQ:STEP 100 MHZ');



fileID = fopen('test30Nov_long_noObject.csv','wt+');  % change name before running another test!!
% Connect to instrument object, obj1.
fopen(obj1);



for k=1:9
    id1=5+0.1*(k-1);
    id2=id1+0.011;
    s=num2str(id1);
    s2=num2str(id2);
    fprintf(fileID,'%s GHz, %s GHz\n',s, s2);
 
    fprintf(obj1,':FREQ:CENT 66 MHz');
    fprintf(obj1,'CALC:MARK:CENT');
    fprintf(obj1,':FREQ:CENT:STEP 11 MHz');
    pause(3);
    for i=1:10
        fprintf(obj1,'CALC:MARK:CENT');
        pause(3);
        fprintf(obj1,'CALC:MARK:Y?');
        pause(1);
        m=fscanf(obj1);
        f=66+(i-1)*11;
        X=[num2str(f), 'MHz =>  ', m];
        m1=num2str(m);
        fprintf(fileID,'%s',m1);

        disp(X);

        fprintf(obj1,':FREQ:CENT UP');
        pause(3);
    end
    
    fprintf(fileID,'\n');
    
    for i=1:18
        for j=1:4
            fprintf(obj1,'CALC:MARK:CENT');
            pause(3);
            fprintf(obj1,'CALC:MARK:Y?');
            pause(1);
            m=fscanf(obj1);
            f=176+(i-1)*11;
            X=[num2str(f), 'MHz =>  ', m];
            m1=num2str(m);
            fprintf(fileID,'%s',m1);

            disp(X);
        end

        fprintf(obj1,':FREQ:CENT UP');
        pause(3);
    end
    
    fprintf(obj3,':FREQ UP');
    fprintf(obj2,':FREQ UP');
    
end 


% Connect to instrument object, obj1.

fprintf(obj2,':FREQ:FIX 4.851 GHz');
fprintf(obj2,':FREQ:STEP 20 MHZ');


% Connect to instrument object, obj1.

fprintf(obj3,':FREQ:FIX 4.84 GHz');
fprintf(obj3,':FREQ:STEP 20 MHZ');



fprintf(obj1,':FREQ:CENT 231 MHz');
fprintf(obj1,'CALC:MARK:CENT');
fprintf(obj1,':FREQ:CENT:STEP 110 MHz');

for k=1:2
  
    fprintf(fileID,'\n');
 
    fprintf(obj3,':FREQ:FIX 4.84 GHz');
    fprintf(obj3,':FREQ:STEP 20 MHZ');
    
    fprintf(obj2,':FREQ:FIX 4.851 GHz');
    fprintf(obj2,':FREQ:STEP 20 MHZ');
    pause(3);
    for i=1:8
        fprintf(obj1,'CALC:MARK:CENT');
        pause(4);
        fprintf(obj1,'CALC:MARK:Y?');
        pause(1);
        m=fscanf(obj1);
        f=(4.84+(i-1)*0.02)*(11+(k)*10);
        X=[num2str(f), 'GHz =>  ', m];
        m1=num2str(m);
        fprintf(fileID,'%s',m1);

        disp(X);
        fprintf(obj3,':FREQ UP');
        fprintf(obj2,':FREQ UP');
        
        pause(3);
    end
    
    fprintf(fileID,'\n');
    
    fprintf(obj1,':FREQ:CENT UP');
    
    
    
end 
fclose(fileID);

