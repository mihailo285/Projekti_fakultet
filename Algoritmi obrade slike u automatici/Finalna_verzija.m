
function vessel_analysis_app
clc
% Inicijalizacija deljenih promenljivih
videoObj = []; % ovde smestam video
videoFile = ''; % ovde cuvam putanju i ime ucitanog fajla
nFrames = 0; % cuvanje ukupnog broja frejmova u videu
frameRate = 1; % cuvanje broja frejmova u sekundi
rectROI = []; % ovde se definise pravougaonik koji korisnik bira
montageImageForROI = []; % promenljiva za cuvanje montazne slike za ROI selekciju
results = []; % tu se cuvaju svi rezultati analize
previewFrame = []; % ovde se cuva slika prvog frejma
scaleFactor = [];

% Pravljenje gui-ja
hFig = figure('Name','Projekat - AOSUA','NumberTitle','off','Position',[100 100 1100 650]);

hAxPreview = axes('Parent',hFig,'Units','pixels','Position',[30 260 480 360]);
title(hAxPreview,'Preview');

hAxFrame = axes('Parent',hFig,'Units','pixels','Position',[540 260 520 360]);
title(hAxFrame,'Frame / Results');

% Dodavanje svih kontrola (dugmadi, teksta...)
uicontrol('Style','pushbutton','String','Load Video','Position',[30 200 120 30],'Callback',@onLoadVideo);
uicontrol('Style','pushbutton','String','Show Montage','Position',[160 200 120 30],'Callback',@onShowMontage);
uicontrol('Style','pushbutton','String','Select ROI','Position',[30 160 120 30],'Callback',@onSelectROI);
uicontrol('Style','pushbutton','String','Process Video','Position',[160 160 120 30],'Callback',@onProcessVideo);
uicontrol('Style','pushbutton','String','Save Results','Position',[30 120 120 30],'Callback',@onSaveResults);
uicontrol('Style','pushbutton','String','Load Results','Position',[160 120 120 30],'Callback',@onLoadResults);
uicontrol('Style','text','Position',[800 200 150 20],'String','Poznata duzina [mm]:');
hEditScaleLength = uicontrol('Style','edit','Position',[780 170 80 28],'String','1'); % Polje za unos duzine
uicontrol('Style','pushbutton','String','Kalibrisi Skalu','Position',[870 170 120 30],'Callback',@onCalibrateScale);

uicontrol('Style','text','Position',[30 90 250 20],'String','Plot: Izaberi index i opciju za plotovanje:');
hEditIndex = uicontrol('Style','edit','Position',[30 60 80 28],'String','1');
uicontrol('Style','pushbutton','String','Plot Point','Position',[120 60 90 28],'Callback',@onPlotPoint);
uicontrol('Style','pushbutton','String','Plot Mean','Position',[220 60 90 28],'Callback',@onPlotMean);

hStatus = uicontrol('Style','text','Position',[350 50 450 28],'String','Status: waiting');

uicontrol('Style','text','Position',[350 220 150 20],'String','Parametri obrade:','HorizontalAlignment','left');
uicontrol('Style','pushbutton','String','Info','Position',[1000 60 80 28],'Callback',@onShowInfo);
uicontrol('Style','text','Position',[350 200 100 20],'String','Bg. removal radius:','HorizontalAlignment','left');
hEditBgRemovalRadius = uicontrol('Style','edit','Position',[460 200 50 28],'String','10'); % Default 10
uicontrol('Style','text','Position',[350 170 100 20],'String','Adaptive N.Size:','HorizontalAlignment','left');
hEditAdaptNSize = uicontrol('Style','edit','Position',[460 170 50 28],'String','21'); % Default 21
uicontrol('Style','text','Position',[350 140 100 20],'String','Morph. Strel. Rad:','HorizontalAlignment','left');
hEditStrelRadius = uicontrol('Style','edit','Position',[460 140 50 28],'String','3'); % Default 3
uicontrol('Style','text','Position',[350 110 100 20],'String','Min Object Area:','HorizontalAlignment','left');
hEditMinObjectArea = uicontrol('Style','edit','Position',[460 110 50 28],'String','200'); % Default 200
uicontrol('Style','text','Position',[540 200 100 20],'String','Skel. PCA Window:','HorizontalAlignment','left');
hEditSkelWindow = uicontrol('Style','edit','Position',[650 200 50 28],'String','5'); % Default 5
hCheckboxVerbose = uicontrol('Style','checkbox','String','Prikazi obradu po frejmu','Position',[540 160 200 20],'Value',0);

% funkcija za ucitavanje videa
    function onLoadVideo(~,~)
        % biram koje ekstenzije prihvatam
        [fname, fpath] = uigetfile({'*.mp4;*.avi;*.mov;*.mpg;*.wmv','Video files (*.mp4,*.avi,...)'; '*.*','All files'}, 'Select video');
        % provera da li je korisnik kliknuo cancel
        if isequal(fname,0), return; end
        videoFile = fullfile(fpath,fname);
        try
            videoObj = VideoReader(videoFile);
        catch ME
            errordlg(['Ne moze se otvoriti video: ' ME.message]);
            return;
        end
        % racunanje ukupnog broja frejmova
        nFrames = floor(videoObj.Duration * videoObj.FrameRate);
        frameRate = videoObj.FrameRate;
        % citanje samo prvog frejma
        previewFrame = read(videoObj, 1);
        imshow(previewFrame, 'Parent', hAxPreview);
        title(hAxPreview, sprintf('Preview: %s', fname), 'Interpreter','none');
        set(hStatus,'String',sprintf('Status: Video ucitan (%d frejmova @ %.2f fps)', nFrames, frameRate));
    end
    % funkcija uzima 3 frejma, sa pocetka, iz sredina i sa kraja i spaja je
    % u jednu dugacku sliku
    function onShowMontage(~,~)
        % provera da li smo kliknuli dugme pre nego sto smo ucitali video
        if isempty(videoObj), errordlg('Prvo ucitaj video!'); return; end
        montageFrameIndices = unique([1, round(nFrames/2), nFrames]); % Sacuvaj indekse
        frames = cell(1,length(montageFrameIndices));
        for i=1:length(montageFrameIndices)
            try
                frames{i} = read(videoObj, montageFrameIndices(i));
            catch
                videoObj.CurrentTime = (montageFrameIndices(i)-1)/videoObj.FrameRate;
                frames{i} = readFrame(videoObj);
            end
        end
        % Kreiraj i sacuvaj montaznu sliku
        montageImage = imtile(frames,'GridSize',[1,length(montageFrameIndices)]);
    
        axes(hAxPreview); imshow(montageImage);
        title(hAxPreview, 'Montazna slika (pocetak, sredina, kraj)');
        set(hStatus,'String','Status: Prikazana montazna slika, izaberite ROI:');
    end

    % funkcija za biranje regiona od interesa
    function onSelectROI(~,~)
        if isempty(videoObj)
            errordlg('Prvo moras ucitati video!');
            return;
        end
    
        % Preuzimam frejmove sa pocetka, sredine i kraja
        idxForMontage = unique([1, round(nFrames/2), nFrames]); % odredjivanje indeka frejmova za montazu
        framesForMontage = cell(1,length(idxForMontage)); % priprema kontejnera za slike
        if isempty(previewFrame) % za dalju konverziju koordinata moram znati dimenziju jednog frejma
            previewFrame = read(videoObj, 1);
        end
        % ucitavam svaki odabrani frejm i cuvam ga
        for i=1:length(idxForMontage)
            try
                framesForMontage{i} = read(videoObj, idxForMontage(i));
            catch
                videoObj.CurrentTime = (idxForMontage(i)-1)/videoObj.FrameRate;
                framesForMontage{i} = readFrame(videoObj);
            end
        end
        
        % spajam ucitane frejmove u jednu sliku i cuvam u deljenoj prom
        montageImageForROI = imtile(framesForMontage,'GridSize',[1,length(framesForMontage)]);
        
        % Prikazujem montazu i omogucujem korisniku da bira ROI
        axes(hAxPreview); imshow(montageImageForROI);
        title(hAxPreview,'Nacrtaj ROI na slici (dupli klik za potvrdu)');
        
        % crtanje pravougaonika za ROI
        h = drawrectangle('StripeColor','r');
        wait(h); % cekam dok korisinik ne uradi dvoklik
        roiMontageCoords = round(h.Position); % ROI koordinate na montazi
        
        % prikaz odabranog pravougaonika na montazi
        rectangle('Position',roiMontageCoords,'EdgeColor','r','LineWidth',1.5,'Parent',hAxPreview);
        set(hStatus,'String',sprintf('Status: Izabran ROI na montazi [x=%.0f y=%.0f w=%.0f h=%.0f]',roiMontageCoords));
        
        % dobijanje dimenzije jednog frejma
        [hFrame, wFrame, ~] = size(previewFrame);
        
        % odredjivanje unutar kog frejma na montazi se nalazi gornji levi
        % ugao ROI
        montageFrameIndex = floor((roiMontageCoords(1) - 1) / wFrame) + 1;
        
        % provera da li je ROI izabran unutar prvog frejma ili nekog drugog
        if montageFrameIndex < 1 || montageFrameIndex > length(idxForMontage)
            errordlg('Izabrani ROI nije validan ili je van granica montaze. Pokusajte ponovo.');
            rectROI = [];
            return;
        end
        
        % racunanje offseta za X koordinatu unutar tog frejma
        offsetX = (montageFrameIndex - 1) * wFrame;
        
        % pretvaranje koordinate ROI-ja sa montaze na individualni frejm
        rectROI = [roiMontageCoords(1) - offsetX, ... % X koordinata unutar frejma
                   roiMontageCoords(2), ...            % Y koordinata (ista za sve frejmove)
                   roiMontageCoords(3), ...            % sirina (ista)
                   roiMontageCoords(4)];               % visina (ista)
        
        % sigurnost da konvertovani ROI bude unutar granica jednog frejma
        rectROI(1) = max(1, rectROI(1));
        rectROI(2) = max(1, rectROI(2));
        rectROI(3) = min(wFrame - rectROI(1) + 1, rectROI(3));
        rectROI(4) = min(hFrame - rectROI(2) + 1, rectROI(4));
    
        set(hStatus,'String',sprintf('Status: ROI izabran (konvertovano na frejm: [x=%.0f y=%.0f w=%.0f h=%.0f])',rectROI));
    end
    
    % funkcija za obradu videa
    function onProcessVideo(~,~)
        if isempty(videoObj) || isempty(rectROI) 
            errordlg('Prvo selektuj video i izaberi ROI.');
            return;
        end
        
        % params struktura sluzi da se svi parametri za obraduslike spakuju
        % na jedno mesto i proslede analyzeFrame funkciji
        params.maxSamplesAlongNormal = ceil(max(rectROI(3:4))*1.1); % ostaje fiksno na osnovu ROI velicine
        params.sampleStep = 0.5; % korak pretrage duz normale, 0.5 znaci da se proverava vrednost piksela na svakih pola piksela
        
        % citanje vrednosti iz gui kontrola
        params.skelWindow = str2double(get(hEditSkelWindow,'String'));
        if isnan(params.skelWindow) || params.skelWindow < 1, params.skelWindow = 5; end % Default
        
        params.minObjectArea = str2double(get(hEditMinObjectArea,'String'));
        if isnan(params.minObjectArea) || params.minObjectArea < 1, params.minObjectArea = 200; end % Default
        
        params.strelRadius = str2double(get(hEditStrelRadius,'String'));
        if isnan(params.strelRadius) || params.strelRadius < 0, params.strelRadius = 3; end % Default
        
        params.bgRemovalRadius = str2double(get(hEditBgRemovalRadius,'String')); 
        if isnan(params.bgRemovalRadius) || params.bgRemovalRadius < 1, params.bgRemovalRadius = 10; end % Default
        
        params.adaptNSize = str2double(get(hEditAdaptNSize,'String')); % Novi parametar
        % za NeighborhoodSize mora biti neparan broj
        if isnan(params.adaptNSize) || params.adaptNSize < 3, params.adaptNSize = 21; end
        if mod(params.adaptNSize,2) == 0, params.adaptNSize = params.adaptNSize + 1; end % Osiguraj neparan broj
        % citanje vrednosti iz checkboxa
        params.verbose = get(hCheckboxVerbose,'Value');
        
        % kreiranje nove, prazne strukture za rezultate
        results = struct();
        results.videoFile = videoFile;
        results.frameRate = frameRate;
        results.nFrames = nFrames;
        results.time = (0:nFrames-1)/frameRate; % kreiranje vremenskog vektora
        results.diametersPerFrame = cell(1,nFrames); % prealokacija memorije, brze nego da sam povecavao niz u svakom koraku petlje
        results.centerlinePerFrame = cell(1,nFrames);
        results.edgeUpperPerFrame = cell(1,nFrames);
        results.edgeLowerPerFrame = cell(1,nFrames);
        
        % waitbar prozor za vizuelni prikaz napretka obrade
        wb = waitbar(0,'Obrada frejmova...');
        for k = 1:nFrames
            try
                frame = read(videoObj, k);
            catch
                videoObj.CurrentTime = (k-1)/videoObj.FrameRate;
                frame = readFrame(videoObj);
            end
            % uzimanje punog frejma i isecanje pravougaonika iz njega
            roiFrame = imcrop(frame, rectROI);
            % pozivanje analyzeFrame funkcije, prosledim joj iseceni frejm
            % i sve parametre i ona vraca rez analize za taj frejm
            [diamVec, centerlinePts, edgeUp, edgeDown] = analyzeFrame(roiFrame, params);
            % postavljanje rezultata u results
            results.diametersPerFrame{k} = diamVec;
            results.centerlinePerFrame{k} = centerlinePts;
            results.edgeUpperPerFrame{k} = edgeUp;
            results.edgeLowerPerFrame{k} = edgeDown;

            % prikaz obrade po frejmu ako sam stiklirao checkbox
            if params.verbose
                axes(hAxFrame); imshow(roiFrame); hold on;
                if ~isempty(centerlinePts)
                    plot(centerlinePts(:,1), centerlinePts(:,2),'g.-','LineWidth',1);
                end
                if ~isempty(edgeUp), plot(edgeUp(:,1), edgeUp(:,2),'r.'); end
                if ~isempty(edgeDown), plot(edgeDown(:,1), edgeDown(:,2),'b.'); end
                title(hAxFrame, sprintf('Frejm %d / %d', k, nFrames));
                hold off;
                drawnow; % azuriranje prikaza odmah
            end
            
            if mod(k,10)==0 % azuriranje statusne trake za svaki 10-i frejm
                set(hStatus,'String',sprintf('Obrada... frejm: %d/%d',k,nFrames));
            end
            waitbar(k/nFrames, wb);
        end
        close(wb);

        set(hStatus,'String','Obrada zavrsena. Mozes sacuvati rezultate ili ih nacrtati (plot).');
        % prolazim kroz sve precnike i racunam prosecan precnik
        meanDiam = nan(1,nFrames);
        for k=1:nFrames
            d = results.diametersPerFrame{k};
            % provera da li imam uopste merenja za ovaj frejm
            if ~isempty(d)
                d_bez_nan = d(~isnan(d)); % ciscenje NaN vrednosti
            % TRIM PROSEK
            % ako ima dovoljno podataka, ukloni ekstremne vrednosti pre racunanja proseka
            if numel(d_bez_nan) > 10 % radim ovo samo ako ima bar 10 tacaka merenja
            
                % sortiram podatke od najmanjeg do najveceg
                d_sorted = sort(d_bez_nan);
            
                % odredjujem koliko procenata podataka sa krajeva treba odbaciti
                trim_percent = 0.20; % odbacujem 20% najmanjih i 20% najvecih vrednosti
                
                % racunam koliko je to zapravo elemenata
                num_elements = numel(d_sorted); 
                num_to_trim = floor(num_elements * trim_percent);
            
                % cuvam samo centralni deo podataka i odredjujem indekse
                start_idx = num_to_trim + 1;
                end_idx = num_elements - num_to_trim;
            
                if start_idx <= end_idx
                    d_trimmed = d_sorted(start_idx:end_idx);
                    meanDiam(k) = mean(d_trimmed); % racunam prosek samo na "dobrim" podacima
                else
                    % ako je nakon odsecanja ostalo 0 podataka, koristim obican prosek
                    meanDiam(k) = mean(d_bez_nan); 
                end
            
            elseif ~isempty(d_bez_nan)
                % ako nemam dovoljno podataka za "trimmed mean", racunam obican prosek
                meanDiam(k) = mean(d_bez_nan);
            else
                % ako su sve vrednosti bile NaN
                meanDiam(k) = NaN;
            end
        
            else
            meanDiam(k) = NaN; % ako je 'd' bio potpuno prazan
            end
        end
        % cuvanje niza prosecnih vrednosti
        results.meanDiameter = meanDiam;
        
        % obezbedjivanje da se poslednji frejm prikaze na kraju ako checkbox nije bio stikliran
        % dakle ovaj blok koda prikazuje rezultat obrade za poslednji frejm
        % kako bi korisnik imao neku vizuelnu potvrdu da je analiza uspela
        if ~params.verbose
             axes(hAxFrame); imshow(imcrop(read(videoObj,nFrames), rectROI)); hold on;
             lastCL = results.centerlinePerFrame{nFrames};
             if ~isempty(lastCL), plot(lastCL(:,1), lastCL(:,2),'g.-','LineWidth',1); end
             up = results.edgeUpperPerFrame{nFrames};
             dn = results.edgeLowerPerFrame{nFrames};
             if ~isempty(up), plot(up(:,1), up(:,2),'r.'); end
             if ~isempty(dn), plot(dn(:,1), dn(:,2),'b.'); end
             hold off;
             title(hAxFrame, sprintf('Rezultati za poslednji frejm (%d)', nFrames));
        end
    end
    % funkcija za cuvanje rezultata
    function onSaveResults(~,~)
        if isempty(results)
            errordlg('Nema rezultata za cuvanje, prvo obradi video.');
            return;
        end
        [fname, fpath] = uiputfile('results.mat','Save results as');
        if isequal(fname,0), return; end
        save(fullfile(fpath,fname),'results','-v7.3');
        set(hStatus,'String',sprintf('Rezultati sacuvani u  %s', fullfile(fpath,fname)));
    end
    % funkcija za ucitavanje rezultata
    function onLoadResults(~,~)
        [fname,fpath] = uigetfile('*.mat','Select results .mat');
        if isequal(fname,0), return; end
        S = load(fullfile(fpath,fname));
        if isfield(S,'results')
            results = S.results;
            set(hStatus,'String',sprintf('Ucitani rezultati iz %s', fullfile(fpath,fname)));
        else
            errordlg('Fajl ne sadrzi ''results'' promenljivu.');
        end
    end
    % funkcija za crtanje precnika tokom vremena za fiksnu tacku
    function onPlotPoint(~,~)
        if isempty(results), errordlg('Prvo ucitaj ili generisi rezultate'); return; end
        idxStr = get(hEditIndex,'String'); idx = str2double(idxStr);
        if isnan(idx) || idx<1, errordlg('Unesi index >= 1'); return; end
        % kreiranje praznog niza za cuvanje nase vremenske serije
        n = results.nFrames;
        series = nan(1,n);
        % petlja za izgradnju serije
        for k=1:n
            % izvlaci vektor svih precnika za k-ti frejm
            d = results.diametersPerFrame{k};
            % provera da li imamo podatke o precniku za ovaj frejm i da li
            % je taj vektor dovoljno dugacak da sadrzi indeks koji korisnik
            % traži
            if ~isempty(d) && numel(d)>=idx
                series(k) = d(idx);
            else
                series(k) = NaN;
            end
        end

        y_data = series;
        y_label = 'Precnik [px]';
    
        % Proveri da li je skala definisana
        if ~isempty(scaleFactor) && scaleFactor > 0
            y_data = series / scaleFactor; % Preracunaj iz piksela u mm
            y_label = 'Precnik [mm]';
        end
    
        figure; plot(results.time, y_data, '-o');
        xlabel('Time [s]'); ylabel(y_label); title(sprintf('Precnik za fiksnu tacku %d kroz vreme', idx));
    end
    
    % funkcija za crtanje prosecnog precnika krvnog suda tokom vremena
    function onPlotMean(~,~)
        if isempty(results), errordlg('Ucitaj ili generisi rezultate prvo'); return; end
        y_data = results.meanDiameter;
        y_label = 'Prosek precnika [px]';
    
        % Proveri da li je skala definisana
        if ~isempty(scaleFactor) && scaleFactor > 0
            y_data = results.meanDiameter / scaleFactor; % Preracunaj iz piksela u mm
            y_label = 'Prosek precnika [mm]';
        end
    
        figure; plot(results.time, y_data, '-o');
        xlabel('Time [s]'); ylabel(y_label); title('Prosecna vrednost precnika kroz vreme');
    end

    % funkcija za obradu slike za jedan frejm
    function [diamVec, centerlinePts, edgeUp, edgeDown] = analyzeFrame(rgbFrame, P)
        % inicijalizacija izlaznih promenljivih
        diamVec = [];
        centerlinePts = [];
        edgeUp = [];
        edgeDown = [];
        % konverzija u sive tonove
        try
            gray = rgb2gray(rgbFrame);
        catch
            gray = rgbFrame;
        end
        % uklanjanje pozadine, sporih, neravnomernih promena u osvetljenju
        sebg = strel('disk', P.bgRemovalRadius); % kreiranje kao neke cetkice za dalje operacije
        bg = imopen(gray, sebg); % prelaskom cetkice preko slike ona ce ukloniti sve svetle objekte koji su manji od cetkice
        I2 = imsubtract(gray, bg); % oduzima procenjenu pozadinu od originalne slike, rez je skoro crna slika a krvni sud je naglasen
        I2 = adapthisteq(I2); % funkcija za poboljsavanje kontrasta na slici gde se mogu dobro videti ivice krvnog suda
        % adaptivna binarizacija
        % racuna razlicit prag za svaki piksel na osnovu osvetljenja u
        % njegovom komsiluku a velicina komslika se kontrolise preko GUI
        T = adaptthresh(I2, 0.5, 'NeighborhoodSize', P.adaptNSize, 'Statistic','gaussian');
        bw = imbinarize(I2, T); % poredi svaki piksel u I2 sa odg pragom u T, ako je piksel svetliji od praga postaje beo inace crn
        % ukoliko je krvni sud tamniji od pozadine binarizacija ce
        % rezultirati crnim sudom na beloj pozadini pa blok ispod to
        % pokusava detektovati
        bw = bwareaopen(bw, P.minObjectArea); % prvo se uklanja sum
        props = regionprops(bw,'Area'); % broje se preostali beli objekti i meri njihova povrsina
        if isempty(props) || sum([props.Area]) < 0.01*numel(bw) % ako nema objekata ili ako je ukupna povrsina svih belih mala
            bw = ~bw; % invertovanje slike 
            bw = bwareaopen(bw, P.minObjectArea); % ponovo se uklanja sum sad na invertovanoj slici
        end
        % finalno ciscenje  
        bw = imclose(bw, strel('disk', P.strelRadius)); % popunjavanje malih rupa i praznina unutar belih objekata
        bw = imfill(bw,'holes'); % dodatno popunjavanje svih rupa unutar objekata bez obzira na njihovu velicinu

        % prvo ukloni bas sitne objekte
        bw = bwareaopen(bw, P.minObjectArea);

        % zadrzavanje samo jednog najveceg objekta
        if any(bw(:)) % proveri da li uopste ima nekih objekata, tj da se ne pozove na potpuno crnoj slici
            bw = bwareafilt(bw, 1);
        end
        % pronalazanje ivice belog objekta
        edgesImg = bwperim(bw);
        % stanjivanje objekta dok ne ostane samo njegova centralna linija
        skel = bwskel(bw);
        skel = bwmorph(skel,'spur',3);
        % pozivanje pomocne funkcije za pretvaranje piksela iz neuredjene
        % gomile u uredjen niz tacaka koje prate centralnu liniju 
        [centerlinePts, ok] = orderSkeleton(skel);
        if ~ok || isempty(centerlinePts) % ako funkcija ne uspe prekida se analiza za ovaj frejm
            diamVec = [];
            edgeUp = [];
            edgeDown = [];
            return;
        end
        % priprema za petlju
        N = size(centerlinePts,1);
        diamVec = nan(N,1);
        edgeUp = nan(N,2);
        edgeDown = nan(N,2);
        [H,W] = size(gray);
        % petlja prolazi kroz svaku tacku uredjene centralne linije i
        % racuna precnik
        for i=1:N
            % uzima se mali segment oko trenutne tacke i
            % w je polu-sirina tog prozora
            x0 = centerlinePts(i,1);
            y0 = centerlinePts(i,2);
            w = P.skelWindow;
            idxlo = max(1,i-w); idxhi = min(N,i+w);
            pts = centerlinePts(idxlo:idxhi,:);
            % proracun tangente pomocu PCA
            pts0 = pts - mean(pts,1);
            if size(pts0,1) < 2
                vx = 1; vy = 0;
            else
                C = (pts0'*pts0);
                [V,D] = eig(C);
                [~,ind] = max(diag(D));
                v = V(:,ind);
                % rezultat je vektor pravca tangente
                vx = v(1); vy = v(2);
            end
            % proracun normale
            nx = -vy; ny = vx;
            normn = hypot(nx,ny); % hyplot racuna duzinu vektora
            % normalizacija
            if normn==0
                nx = 1; ny = 0;
            else
                nx = nx/normn; ny = ny/normn;
            end
            % priprema za pretragu
            maxT = P.maxSamplesAlongNormal;
            t_vals = 0:P.sampleStep:maxT; % niz vrednosti koje predstavljaju udaljenost od centralne linije
            posFound = false; negFound = false;
            posCoord = []; negCoord = [];
            % pretraga u pozitivnom smeru normale
            for t = t_vals
                xx = x0 + t*nx; yy = y0 + t*ny;
                xi = round(xx); yi = round(yy);
                if xi < 1 || xi > W || yi < 1 || yi > H, break; end
                if edgesImg(yi, xi)
                    posFound = true;
                    posCoord = [xx yy];
                    break;
                end
            end
            % pretraga u negativnom smeru normale
            for t = t_vals
                xx = x0 - t*nx; yy = y0 - t*ny;
                xi = round(xx); yi = round(yy);
                if xi < 1 || xi > W || yi < 1 || yi > H, break; end
                if edgesImg(yi, xi)
                    negFound = true;
                    negCoord = [xx yy];
                    break;
                end
            end
            % ako su pronadjene obe ivice racuna se euklidsko rastojanje
            % izmedju njih, to je zapravo precnik, i upisuju se vrednosti u
            % izlazne nizove ako bilo koja ivica nije pronadjena pisemo Nan
            if posFound && negFound
                d = hypot(posCoord(1)-negCoord(1), posCoord(2)-negCoord(2));
                diamVec(i) = d;
                edgeUp(i,:) = posCoord;
                edgeDown(i,:) = negCoord;
            else
                diamVec(i) = NaN;
                edgeUp(i,:) = [NaN NaN];
                edgeDown(i,:) = [NaN NaN];
            end
        end
    end
    % pomocna funkcija za racunanje tangente i normale
    function [orderedPts, ok] = orderSkeleton(skelBW)
        % inicijalizacija izlaznih promenljivih
        ok = false; % ako funkcija dobro obavi posao tad će ok biti true
        orderedPts = []; % ovde smestam konacni uredjeni niz tacaka
        [ys,xs] = find(skelBW); % funkcija koja pronalazi sve piksele koji nisu nula i vraca njihove koordinate
        if isempty(xs), return; end % ako nema sta da se radi funkcija se odmah prekida
        coords = [xs ys];
        endpoints = bwmorph(skelBW,'endpoints'); % pronalazim sve krajnje tacke na skeletu
        [ey,ex] = find(endpoints);
        if numel(ex) >= 1 % ako je pronadjena bar jedna krajnja tacka
            start = [ex(1), ey(1)]; % uzimam prvu pronadjenu krajnju tacku kao pocetnu tacku
        else
           % ako nema krajnjih tacaka uzimam prvu tacku iz neuredjene liste      
            start = coords(1,:);
        end
        N = size(coords,1); % ukupan broj tacaka na skeletu
        visited = false(N,1); % kreiram logicki niz posecenosti
        orderedPts = zeros(N,2); % prealociram memoriju za konacni uredjeni niz
        orderedPts(1,:) = start; % postavljam prvu tacku u uredjenom nizu da bude pocetna tacka
        % pronalazim pocetnu tacku u originalnom nizu da je oznacim kao
        % posecenu
        dists = hypot(coords(:,1)-start(1), coords(:,2)-start(2)); % racunam rastojanje od pocetne tacke do svih ostalih tacaka
        [~, idx] = min(dists); % pronalazim indeks tacke koja ima minimalno rastojanje
        visited(idx) = true; % oznacim tu tacku kao posecenu
        curr = start; % postavljam trenutnu poziciju na pocetnu tacku
        % petlja se ponavlja N-1 puta da pronadjem sve preostale tacke
        for k=2:N
            % pronalazenje svih neposecenih tacaka koji su direktni susedi
            % trenutne tacke 
            neigh = [];
            for j=1:N
                if ~visited(j)
                    if max(abs(coords(j,:) - curr)) <= 1 
                        neigh(end+1) = j; %#ok<AGROW>
                    end
                end
            end
            % ako postoje direktni susedi
            if ~isempty(neigh)
                ncoords = coords(neigh,:);
                dd = hypot(ncoords(:,1)-curr(1), ncoords(:,2)-curr(2)); % ako postoji vise od jednog neposecenog suseda ovaj kod bira onog koji je fizicki najblizi trenutnoj tacki
                [~,m] = min(dd);
                chosen = neigh(m); % indeks izabranog suseda
            % ako ne postoje direktni susedi
            else
                % u ovom slucaju algoritam skace na najblizu neposecenu
                % tacku bilo gde na slici
                unvisIdx = find(~visited);
                if isempty(unvisIdx), break; end
                dd = hypot(coords(unvisIdx,1)-curr(1), coords(unvisIdx,2)-curr(2));
                [~,m] = min(dd);
                chosen = unvisIdx(m);
            end

            orderedPts(k,:) = coords(chosen,:); % dodajem izabranu tacku u moj uredjeni niz
            curr = coords(chosen,:); % pomeram trenutnu poziciju na tu novu tacku
            visited(chosen) = true; % oznacavam je kao posecenu da se ne bih vracao na nju
        end
        orderedPts = orderedPts(any(orderedPts,2),:); % ova linija uklanja sve redove koji sadrze samo nule
        ok = true; % ako je sve proslo postavljam ok na true
    end
    % pomocna funkcija za prikaz informacija o parametrima
    function onShowInfo(~,~)
        % kreiranje teksta koji ce biti prikazan
        % cell niz se koristi da bi svaka linija teksta bila u novom redu
        helpText = {
            '--- Informacije o parametrima obrade ---'
            ''
            'Bg. removal radius:'
            '• Radi za uklanjanje pozadine (imopen).'
            '• Uklanja neujednačeno osvetljenje.'
            '• Preporučeni opseg: 5 - 30'
            ''
            'Adaptive N.Size:'
            '• Veličina komšiluka za adaptivnu binarizaciju.'
            '• Veća vrednost ignoriše sitnu teksturu i daje glađe ivice.'
            '• Preporučeni opseg: 21 - 101 (mora biti neparan broj!)'
            ''
            'Morph. Strel. Rad:'
            '• Radi za morfološko zatvaranje (imclose).'
            '• Popunjava rupe i prekide u krvnom sudu.'
            '• Preporučeni opseg: 3 - 10'
            ''
            'Min Object Area:'
            '• Minimalna površina objekta (u pikselima) da bi bio zadržan.'
            '• Uklanja sitan šum nakon binarizacije.'
            '• Preporučeni opseg: 200 - 5000 (zavisi od rezolucije)'
            ''
            'Skel. PCA Window:'
            '• Veličina prozora za računanje tangente na skeletu.'
            '• Veća vrednost daje glađe, ali manje precizne tangente.'
            '• Preporučeni opseg: 3 - 15'
            ''
            };
        
        % prikazujem tekst u 'help' dijalog prozoru.
        helpdlg(helpText, 'Informacije o Parametrima');
    end
    % pomocna funkcija za preracunavanje piksela u milimetre
    function onCalibrateScale(~,~)
        if isempty(previewFrame)
            errordlg('Prvo ucitajte video da bi se prikazao prvi frejm za kalibraciju.');
            return;
        end
        
        % citam poznatu duzinu koju je korisnik uneo
        knownLengthStr = get(hEditScaleLength, 'String');
        knownLength_mm = str2double(knownLengthStr);
        if isnan(knownLength_mm) || knownLength_mm <= 0
            errordlg('Unesite validnu, pozitivnu vrednost za poznatu duzinu u mm.');
            return;
        end
        
        % prikazujem prvi frejm i govorim korisniku sta treba da uradi
        axes(hAxPreview); imshow(previewFrame);
        title(hAxPreview, 'Nacrtajte liniju preko objekta poznate duzine. Dupli klik za kraj.');
        
        % omogucavam korisniku da nacrta liniju
        hLine = drawline('Color','cyan','LineWidth',2);
        wait(hLine); % cekam da korisnik zavrsi (dupli klik)
        pos = hLine.Position;
        

        % racunam duzinu nacrtane linije u pikselima
        p1 = pos(1,:); % [x1, y1]
        p2 = pos(2,:); % [x2, y2]
        length_px = hypot(p2(1)-p1(1), p2(2)-p1(2));
        
        if length_px < 1
            errordlg('Nacrtana linija je prekratka. Pokusajte ponovo.');
            delete(hLine);
            return;
        end
        
        % racunam i cuvam faktor skaliranja
        scaleFactor = length_px / knownLength_mm; % rezultat je u [piksel / mm]
        
        delete(hLine); % uklanjam liniju sa slike nakon kalibracije
        
        % prikaz poruke da smo uspeli
        msg = sprintf('Kalibracija uspesna!\nFaktor skale: %.2f px/mm', scaleFactor);
        msgbox(msg, 'Skala Definisana');
        set(hStatus,'String',sprintf('Status: Skala definisana (%.2f px/mm)', scaleFactor));
        
        % vracam originalni naslov na preview prozor
        title(hAxPreview, sprintf('Preview: %s', videoFile), 'Interpreter','none');
    end

end
