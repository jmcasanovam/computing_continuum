package com.hdrescuer.hdrescuer.ui.ui.devicesconnection;

import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.FragmentManager;
import androidx.fragment.app.FragmentTransaction;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.ResultReceiver;
import android.provider.Settings;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import android.os.Looper;

import com.hdrescuer.hdrescuer.retrofit.AuthApiService;
import com.hdrescuer.hdrescuer.retrofit.AuthConectionClient;
import retrofit2.Retrofit;
import retrofit2.Response;

import com.empatica.empalink.ConnectionNotAllowedException;
import com.empatica.empalink.EmpaDeviceManager;
import com.empatica.empalink.EmpaticaDevice;
import com.empatica.empalink.config.EmpaSensorType;
import com.empatica.empalink.config.EmpaStatus;
import com.empatica.empalink.delegate.EmpaStatusDelegate;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.android.gms.wearable.CapabilityClient;
import com.google.android.gms.wearable.CapabilityInfo;
import com.google.android.gms.wearable.DataClient;
import com.google.android.gms.wearable.DataEvent;
import com.google.android.gms.wearable.DataEventBuffer;
import com.google.android.gms.wearable.DataItem;
import com.google.android.gms.wearable.DataMap;
import com.google.android.gms.wearable.DataMapItem;
import com.google.android.gms.wearable.PutDataMapRequest;
import com.google.android.gms.wearable.PutDataRequest;
import com.google.android.gms.wearable.Wearable;
import com.google.android.gms.wearable.Node;
import com.hdrescuer.hdrescuer.R;
import com.hdrescuer.hdrescuer.common.Constants;
import com.hdrescuer.hdrescuer.common.OnSimpleDialogClick;
import com.hdrescuer.hdrescuer.common.SimpleDialogFragment;
import com.hdrescuer.hdrescuer.data.dbrepositories.E4BandRepository;
import com.hdrescuer.hdrescuer.data.dbrepositories.EHealthBoardRepository;
import com.hdrescuer.hdrescuer.data.GlobalMonitoringViewModel;
import com.hdrescuer.hdrescuer.data.dbrepositories.SessionsRepository;
import com.hdrescuer.hdrescuer.data.dbrepositories.TicWatchRepository;
import com.hdrescuer.hdrescuer.db.entity.SessionEntity;
import com.hdrescuer.hdrescuer.ui.ui.charts.SessionResultActivity;
import com.hdrescuer.hdrescuer.ui.ui.devicesconnection.devicesconnectionmonitoring.DevicesMonitoringFragment;
import com.hdrescuer.hdrescuer.ui.ui.devicesconnection.services.EhealthBoardThread;
import com.hdrescuer.hdrescuer.ui.ui.devicesconnection.services.SampleRateFilterThread;
import com.hdrescuer.hdrescuer.ui.ui.devicesconnection.services.StartStopSessionService;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.Method;
import java.text.SimpleDateFormat;
import java.time.Clock;
import java.time.Instant;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.Set;

/**
 * Clase DevicesConnectionActivity. Es el núcleo de la aplicación. Es
 * responsable de buscar los dispositivos e implementar distintas librerías para
 * la interacción con ellos
 * 
 * @author Domingo Lopez
 */
public class DevicesConnectionActivity extends AppCompatActivity implements
        View.OnClickListener, EmpaStatusDelegate,
        CapabilityClient.OnCapabilityChangedListener,
        DataClient.OnDataChangedListener {

    // Indicador de sesión crashed
    public static boolean crashed = false;

    // Repositorios
    E4BandRepository e4BandRepository;
    TicWatchRepository ticWatchRepository;
    EHealthBoardRepository eHealthBoardRepository;
    SessionsRepository sessionsRepository;

    // ViewModel
    GlobalMonitoringViewModel globalMonitoringViewModel;

    AuthApiService authApiService;

    TextView tvUsernameMonitoring;
    TextView tvDateMonitoring;
    ImageView btn_back;
    // Botones de conexión
    Button btnE4BandConnect;
    Button btnWatchConnect;
    Button btnEHealthBoardConnect;
    ImageView btn_connection_up;
    // Botón de start monitoring
    Button btnStartMonitoring;

    // Datos del paciente actual
    int user_id;
    String user_name;
    Date currentDate;

    // Atributos para la conexión con la E4BAND
    private static final int REQUEST_ENABLE_BT = 1;
    private static final int REQUEST_PERMISSION_ACCESS_COARSE_LOCATION = 1;
    private EmpaDeviceManager deviceManager = null;

    // Atributos para la detección del Watch
    private Set<Node> wearNodesWithApp;
    private List<Node> allConnectedNodes;

    // Atributos de compartición de datos entre la capa de datos del reloj y la app
    /** Capa de datos para la compartición de los mismos entre el Watch y la App **/
    private DataClient dataClient;
    // Atributos de compartición de datos para cada uno de los sensores
    private static final String MONITORING_KEY = "MONITORING";
    private static final String MONITORINGSTOP_KEY = "MONITORINGSTOP";
    PutDataMapRequest putDataMapRequest = PutDataMapRequest.create("/MONITORING");
    PutDataRequest putDataReq;
    PutDataMapRequest putDataMapRequestStop = PutDataMapRequest.create("/MONITORINGSTOP");
    PutDataRequest putDataReqStop;

    // Atributos para la detección y recepción de datos de la placa
    BluetoothAdapter bluetoothAdapter;
    BluetoothDevice ehealthBoardDevice;
    BluetoothSocket bluetoothSocket;
    InputStream myInputStream;
    OutputStream myOutStream;
    String macAddress = "00:14:03:05:0C:99";

    // Hebra para el envío de datos al servidor
    private SampleRateFilterThread sampleRateThread;
    // Hebra/Servicio que recibirá los datos vía Bluetooth del eHealthBoard
    private EhealthBoardThread ehealthBoardThread;

    // Estado de los dispositivos
    boolean e4Connected = false;
    boolean ticwatchConnected = false;
    boolean ehealthConnected = false;

    // TimeStamp
    Instant instant;

    // Identificador de sesión
    int session_id;

    // Descripción de la sesión (Para el modo no conexión)
    String session_description;

    // Sesión sincronizada o no
    boolean sync;

    // Formato para fecha
    SimpleDateFormat format = new SimpleDateFormat("dd/MM/yyyy HH:mm");

    /**
     * Método onCreate de la Activity. Recibe un intent e incializa los viewModels,
     * las vistas, eventos y carga los datos iniciales de los elementos de la vista
     * 
     * @author Domingo Lopez
     * @param savedInstanceState
     */
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_devices_connection);

        // Ocultamos el Toolbar del MainActivity para el login
        getSupportActionBar().hide();

        // Obtenemos el id del usuario
        if (Constants.CONNECTION_UP.equals("SI")) {
            Intent i = getIntent();
            this.user_id = i.getIntExtra("user_id", 0);
            this.user_name = i.getStringExtra("username");
            this.sync = true;
        } else {
            this.sync = false;
            if (Constants.CONNECTION_MODE.equals("FASTMODE")) {
                this.user_id = 0;
                this.user_name = "Fast Mode";

            } else {
                Intent i = getIntent();
                this.user_id = i.getIntExtra("user_id", 0);
                this.user_name = i.getStringExtra("username");
            }
        }

        // Obtenemos la fecha:hora actual
        this.currentDate = Calendar.getInstance().getTime();

        initViewModels();
        // Inicializar AuthApiService aquí también
        this.authApiService = AuthConectionClient.getInstance().getAuthApiService(); // <-- Inicializar AuthApiService
        findViews();
        events();
        loadUserData();
        initEmpaticaDeviceManager();

    }

    /**
     * En el onResume, iniciamos el dataClient para interacción con el Watch, y
     * buscamos todos los dispositivos con WearOs que tengan nuestra app instalada
     * 
     * @author Domingo Lopez
     */
    @Override
    protected void onResume() {
        super.onResume();
        DevicesConnectionActivity.crashed = false;
        Wearable.getCapabilityClient(this).addListener(this, Constants.CAPABILITY_WEAR_APP);
        this.dataClient = Wearable.getDataClient(this);
        Wearable.getDataClient(this).addListener(this);
        // Initial request for devices with our capability, aka, our Wear app installed.
        findWearDevicesWithApp();
        findAllWearDevices();

    }

    /**
     * Busca la placa de salud y se intenta conectar por bluetooth
     * 
     * @author Domingo Lopez
     * @return boolean
     */
    private boolean conectareHealthBoardBT() {
        try {
            if (this.bluetoothAdapter.isEnabled()) {
                this.bluetoothAdapter.startDiscovery();
                this.ehealthBoardDevice = this.bluetoothAdapter.getRemoteDevice(this.macAddress);
                BluetoothSocket tmp = null;
                try {
                    // Obtenemos el método de la clase BluetoothDevice
                    Method m = this.ehealthBoardDevice.getClass().getMethod("createRfcommSocket",
                            new Class[] { int.class });
                    tmp = (BluetoothSocket) m.invoke(this.ehealthBoardDevice, Integer.valueOf(1));
                } catch (Exception e) {
                    e.printStackTrace();
                    Log.i("BOARD_ERROR", "La conexión del socket tmp no ha funcionado");
                    Toast.makeText(this, "Error al conectar con la placa eHealth", Toast.LENGTH_SHORT).show();
                    this.ehealthConnected = false;
                    return false;
                }

                this.bluetoothSocket = tmp;
                try {
                    this.bluetoothSocket.connect();
                } catch (Exception e) {
                    e.printStackTrace();
                    Log.i("BOARD_ERROR", "No se ha podido crear el socket bluetooth");
                    Toast.makeText(this, "Error al conectar con la placa eHealth", Toast.LENGTH_SHORT).show();
                    this.ehealthConnected = false;
                    return false;
                }
                try {
                    this.myInputStream = this.bluetoothSocket.getInputStream();
                } catch (Exception e) {
                    Log.i("BOARD_ERROR", "Error " + e.getMessage());
                    Toast.makeText(this, "Error al conectar con la placa eHealth", Toast.LENGTH_SHORT).show();
                    this.ehealthConnected = false;
                    return false;
                }

                try {
                    this.myOutStream = this.bluetoothSocket.getOutputStream();
                } catch (Exception e) {
                    Log.i("BOARD_ERROR", "Error " + e.getMessage());
                    Toast.makeText(this, "Error al conectar con la placa eHealth", Toast.LENGTH_SHORT).show();
                    this.ehealthConnected = false;
                    return false;
                }

                Log.i("BOARD_OK", "Conectado a la placa");
                this.ehealthConnected = true;
            }
        } catch (Exception e) {
            e.printStackTrace();
            Log.i("BOARD_ERROR", "No se ha podido conectar a la placa");
            Toast.makeText(this, "Error al conectar con la placa eHealth", Toast.LENGTH_SHORT).show();
            this.ehealthConnected = false;
            return false;
        }
        return this.ehealthConnected;
    }

    /**
     * Inicializa todos los viewmodels de los que haremos uso
     * 
     * @author Domingo Lopez
     */
    private void initViewModels() {

        // iniciamos Repositorios temporales
        this.e4BandRepository = new E4BandRepository(getApplication());
        this.ticWatchRepository = new TicWatchRepository(getApplication());
        this.eHealthBoardRepository = new EHealthBoardRepository(getApplication());
        this.sessionsRepository = new SessionsRepository(getApplication());

        // ViewModelFactory para el repositorio Global
        ViewModelProvider.Factory factory = new ViewModelProvider.Factory() {
            @NonNull
            @Override
            public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {
                return (T) new GlobalMonitoringViewModel(getApplication(), user_id);
            }
        };
        this.globalMonitoringViewModel = new ViewModelProvider(this, factory).get(GlobalMonitoringViewModel.class);

    }

    /**
     * Busca los elementos de la vista de interfaz y los inicializa
     * 
     * @author Domingo Lopez
     */
    private void findViews() {

        this.tvUsernameMonitoring = findViewById(R.id.tvUserNameToolbarMonitoring);
        this.btn_back = findViewById(R.id.btn_back_new_monitoring);
        this.tvDateMonitoring = findViewById(R.id.tv_date_monitoring);
        this.btnStartMonitoring = findViewById(R.id.btn_start_monitoring);
        this.btn_connection_up = findViewById(R.id.btn_connection_up);
        if (Constants.CONNECTION_UP.equals("SI")) {
            this.btn_connection_up.setImageDrawable(getDrawable(R.drawable.ic_baseline_wifi_24_green));
        } else {
            this.btn_connection_up.setImageDrawable(getDrawable(R.drawable.ic_baseline_wifi_24_red));
        }

        // Botones para la conexión de los dispositivos

        // E4BAND
        this.btnE4BandConnect = findViewById(R.id.btn_connect_e4);

        // WATCH.
        this.btnWatchConnect = findViewById(R.id.btn_connect_watch);

        // EHealthBoard
        this.btnEHealthBoardConnect = findViewById(R.id.btn_connect_ehealthboard);
        this.btnEHealthBoardConnect.setOnClickListener(this);
    }

    /**
     * Inicializa los eventos de click
     * 
     * @author Domingo Lopez
     */
    private void events() {
        this.btn_back.setOnClickListener(this);
        this.btnStartMonitoring.setOnClickListener(this);
    }

    /**
     * Carga los datos iniciales de la vista
     * 
     * @author Domingo Lopez
     */
    private void loadUserData() {

        // Iniciamos las views a los valores iniciales por defecto
        this.tvUsernameMonitoring.setText(this.user_name);
        this.tvDateMonitoring.setText(this.format.format(this.currentDate));

        // Botón de la empática
        this.btnE4BandConnect
                .setBackgroundColor(this.btnE4BandConnect.getContext().getResources().getColor(R.color.e4Connecting));
        this.btnE4BandConnect.setText("Detectando");

        // Botón del watch
        this.btnWatchConnect
                .setBackgroundColor(this.btnWatchConnect.getContext().getResources().getColor(R.color.e4Connecting));
        this.btnWatchConnect.setText("Detectando");

        // Botón de la ehealthBoard
        this.btnEHealthBoardConnect.setBackgroundColor(
                this.btnEHealthBoardConnect.getContext().getResources().getColor(R.color.e4disconnected));
        this.btnEHealthBoardConnect.setText("Pulsa para conectar");

    }

    /**
     * Método para comprobar si se tienen permisos de Bluetooth. Si no se tienen
     * lanza un dialog que avisa al usuario para que los active
     * 
     * @author Domingo Lopez
     */
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
            @NonNull int[] grantResults) {
        switch (requestCode) {
            case REQUEST_PERMISSION_ACCESS_COARSE_LOCATION:
                // Si se cancela la eleccion de permisos, no se llena el array
                if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    // Permisos concedidos
                    initEmpaticaDeviceManager();
                } else {
                    // Permission denied
                    final boolean needRationale = ActivityCompat.shouldShowRequestPermissionRationale(this,
                            Manifest.permission.ACCESS_COARSE_LOCATION);
                    new AlertDialog.Builder(this)
                            .setTitle("Permisos requeridos")
                            .setMessage(
                                    "Sin estos permisos no podemos localizar los dispositivos bluetooth, Permite el acceso a estos permisos para utilizar la aplicación")
                            .setPositiveButton("Volver a intentarlo", new DialogInterface.OnClickListener() {
                                public void onClick(DialogInterface dialog, int which) {
                                    // try again
                                    if (needRationale) {
                                        initEmpaticaDeviceManager();
                                    } else {
                                        Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                                        Uri uri = Uri.fromParts("package", getPackageName(), null);
                                        intent.setData(uri);
                                        startActivity(intent);
                                    }
                                }
                            })
                            .setNegativeButton("Salir ", new DialogInterface.OnClickListener() {
                                public void onClick(DialogInterface dialog, int which) {
                                    // Si no tenemos permisos salimos a la actividad anterior
                                    finish();
                                }
                            })
                            .show();
                }
                break;
        }
    }

    /**
     * Método que inicia el dispositivo Empatica Band. Inicia la empatica con el
     * APIKEY que tenemos guardado en Constants
     * 
     * @author Domingo Lopez
     */
    private void initEmpaticaDeviceManager() {
        // Android 6 (API level 23) now require ACCESS_COARSE_LOCATION permission to use
        // BLE
        if (ContextCompat.checkSelfPermission(this,
                Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[] { Manifest.permission.ACCESS_COARSE_LOCATION },
                    REQUEST_PERMISSION_ACCESS_COARSE_LOCATION);
        } else {
            if (TextUtils.isEmpty(Constants.EMPATICA_API_KEY)) {
                new AlertDialog.Builder(this)
                        .setTitle("Warning")
                        .setMessage("Please insert your API KEY")
                        .setNegativeButton("Close", new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int which) {
                                // without permission exit is the only way
                                finish();
                            }
                        })
                        .show();
                return;
            }

            // Creamos el deviceManager y hacemos que el ViewModel que vamos a compartir con
            // el fragment de monitorización obtenga los datos
            deviceManager = new EmpaDeviceManager(getApplicationContext(), this.e4BandRepository, this);

            // Initialize the Device Manager using your API key. You need to have Internet
            // access at this point.
            deviceManager.authenticateWithAPIKey(Constants.EMPATICA_API_KEY);

        }
    }

    /**
     * Gestor de eventos de click para los elementos de la vista
     * 
     * @author Domingo Lopez
     * @param v
     */
    @Override
    public void onClick(View v) {

        switch (v.getId()) {
            case R.id.btn_back_new_monitoring:

                // Hay una sesión en marcha. Paramos los dispositivos
                if (this.sampleRateThread != null && SampleRateFilterThread.STATUS.equals("ACTIVO")) {
                    // Paramos las hebras que pudiera haber activas
                    SampleRateFilterThread.STATUS = "INACTIVO";
                    EhealthBoardThread.STATUS = "INACTIVO";

                    Intent intent = new Intent(this, StartStopSessionService.class);

                    if (Constants.CONNECTION_MODE == "STREAMING" && Constants.CONNECTION_UP.equals("SI")) {
                        intent.setAction("STOP_SESSION");
                    } else {
                        intent.setAction("STOP_OFFLINE_MODE");
                    }
                    String instant = Clock.systemUTC().instant().toString();
                    intent.putExtra("session_id", session_id);
                    intent.putExtra("timestamp_fin", instant);
                    intent.putExtra("receiver", sessionResult);

                    this.startService(intent);
                } else {
                    DevicesConnectionActivity.crashed = false;
                    String timeback = String.valueOf(System.currentTimeMillis());
                    this.putDataMapRequestStop.getDataMap().putString(MONITORINGSTOP_KEY, timeback);
                    this.putDataReqStop = this.putDataMapRequestStop.asPutDataRequest();
                    Task<DataItem> putDataTask1 = this.dataClient.putDataItem(this.putDataReqStop);
                    putDataTask1.addOnCompleteListener(new OnCompleteListener<DataItem>() {
                        @Override
                        public void onComplete(@NonNull Task<DataItem> task) {
                            Log.i("INFOTASK", "PUESTO VALOR STOP MONITORING EN DATACLIENT");
                        }
                    });
                    EhealthBoardThread.STATUS = "INACTIVO";
                    SampleRateFilterThread.STATUS = "INACTIVO";
                    finish();
                }

                break;

            case R.id.btn_start_monitoring:

                int devices_counter = getTotalConnectedDevices();

                if (devices_counter == 0) {
                    Toast.makeText(this,
                            "No hay dispositivos conectados, debe conectar alguno antes de empezar la sesión",
                            Toast.LENGTH_SHORT).show();
                } else {

                    SimpleDialogFragment dialogFragment = new SimpleDialogFragment(new OnSimpleDialogClick() {
                        @Override
                        public void onPositiveButtonClick(String description) {
                            session_description = description;
                            initSession();
                        }

                        @Override
                        public void onPositiveButtonClick() {
                        }

                        @Override
                        public void onNegativeButtonClick() {
                        }
                    }, "SET_DESCRIPTION");

                    dialogFragment.show(getSupportFragmentManager(), null);

                }

                break;

            case R.id.btn_connect_ehealthboard:

                if (this.ehealthConnected) {
                    this.ehealthConnected = false;
                    this.btnEHealthBoardConnect.setBackgroundColor(
                            this.btnEHealthBoardConnect.getContext().getResources().getColor(R.color.e4disconnected));
                    this.btnEHealthBoardConnect.setText("Pulsa para Conectar");
                    this.bluetoothAdapter.cancelDiscovery();
                    try {
                        this.bluetoothSocket.close();
                    } catch (Exception e) {
                        Log.i("ERRORSOCKET", "Error al cerrar socket bluetooth ehealthBoard");
                    }
                } else {
                    this.bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
                    boolean conectado = conectareHealthBoardBT();
                    if (conectado) {
                        this.bluetoothAdapter.cancelDiscovery();
                        this.btnEHealthBoardConnect.setBackgroundColor(
                                this.btnEHealthBoardConnect.getContext().getResources().getColor(R.color.e4connected));
                        this.btnEHealthBoardConnect.setText("Conectado");
                    }
                }

                break;

        }
    }

    /**
     * Método que devuelve el total de dispositivos conectados
     * 
     * @author Domingo Lopez
     * @return int
     */
    int getTotalConnectedDevices() {
        int devices_counter = 0;
        if (this.e4Connected)
            devices_counter++;
        if (this.ticwatchConnected)
            devices_counter++;
        if (this.ehealthConnected)
            devices_counter++;

        this.e4BandRepository.setConnected(e4Connected);
        this.ticWatchRepository.setConnected(ticwatchConnected);
        this.eHealthBoardRepository.setConnected(ehealthConnected);

        return devices_counter;
    }

    /**
     * Método que llama al servicio encargado de iniciar la sesión de entrenamiento
     * del usuario. Hace uso de un ResultReceiver para conocer el resultado de la
     * operación contra el servidor
     * 
     * @author Domingo Lopez
     */
    @RequiresApi(api = Build.VERSION_CODES.O)
    void initSession() {

        Intent intent = new Intent(this.getApplicationContext(), StartStopSessionService.class);
        this.instant = Clock.systemUTC().instant();

        // Obtengo el id máximo de sesión local
        int max_id = sessionsRepository.getMaxSession();
        // Log.i("MAXIMA SESION",""+max_id);
        if (max_id >= 1) {
            session_id = max_id + 1;
        } else { // si no hay sesiones. La inicio a 1
            session_id = 1;
        }

        if (Constants.CONNECTION_MODE == "STREAMING" && Constants.CONNECTION_UP.equals("SI")) {
            intent.setAction("START_SESSION");
            intent.putExtra("session_id", session_id);
            intent.putExtra("user_id", this.user_id);
            intent.putExtra("timestamp_ini", this.instant.toString());
            intent.putExtra("e4band", this.e4Connected);
            intent.putExtra("ticwatch", this.ticwatchConnected);
            intent.putExtra("ehealthboard", this.ehealthConnected);
            intent.putExtra("description", this.session_description);
            intent.putExtra("receiver", this.sessionResult);
        } else {
            intent.setAction("START_OFFLINE_MODE");
            intent.putExtra("receiver", this.sessionResult);
        }

        this.startService(intent);
    }

    public ResultReceiver sessionResult = new ResultReceiver(new Handler(Looper.getMainLooper())) {
        @Override
        protected void onReceiveResult(int resultCode, Bundle resultData) {
            super.onReceiveResult(resultCode, resultData);
            // Maneja el código de resultado del servicio según la lógica (éxito/error)
            switch (resultCode) {
                case 1: // Caso correcto: Sesión iniciada

                    // Guardamos la sesión en la BD
                    initDBLocalSession();

                    if (bluetoothAdapter != null) {
                        bluetoothAdapter.cancelDiscovery();
                    }

                    /** INICIO DEL RELOJ **/
                    if (ticwatchConnected) {
                        // NO PODEMOS PONER EL MISMO VALOR AL MANDAR EL DATO, SI PONEMOS EL MISMO VALOR,
                        // EL ONCHANGED NO SE RECIBE. POR TANTO HEMOS DE HACER UN TIMESTAMP Y MANDARLO
                        String timeStart = String.valueOf(System.currentTimeMillis());
                        putDataMapRequest.getDataMap().putString(MONITORING_KEY, timeStart);
                        putDataReq = putDataMapRequest.asPutDataRequest();
                        Task<DataItem> putDataTask = dataClient.putDataItem(putDataReq);
                        putDataTask.addOnCompleteListener(new OnCompleteListener<DataItem>() {
                            @Override
                            public void onComplete(@NonNull Task<DataItem> task) {
                                Log.i("INFOTASK", "PUESTO VALOR START MONITORING EN DATACLIENT");
                            }
                        });
                    }

                    /** INICIO DE LA EHEALTHBOARD **/
                    if (ehealthConnected) { // Si está conectada
                        initEHeatlhBoard(); // Solo hace el inicio para mandar una instrucción de inicio al arduino
                        EhealthBoardThread.STATUS = "ACTIVO";
                        ehealthBoardThread = new EhealthBoardThread(eHealthBoardRepository, myInputStream, myOutStream);
                        ehealthBoardThread.start();
                    } else {
                        EhealthBoardThread.STATUS = "INACTIVO";
                    }

                    /** REINICIAMOS LOS REPOSITORIOS **/
                    // Seteamos los repositorios para la nueva sesión
                    resetRepositories();

                    // *** ESTE ES EL ÚNICO LUGAR DONDE SE DEBE INICIAR SampleRateFilterThread y
                    // DevicesMonitoringFragment ***
                    // Iniciamos proceso en Background para lectura de datos según el sample rate
                    // que le pongamos
                    // Y el Fragment de monitorización SOLO DESPUÉS de intentar obtener la IP del
                    // nodo.
                    getInitialStreamingNodeIp(new Runnable() {
                        @Override
                        public void run() {
                            // Este código se ejecutará en el hilo principal DESPUÉS de que
                            // getInitialStreamingNodeIp
                            // haya terminado y haya actualizado Constants.CURRENT_STREAMING_NODE_IP
                            if (Constants.CURRENT_STREAMING_NODE_IP != null) {
                                // Solo si se asignó un nodo de streaming válido, iniciamos el hilo de datos
                                SampleRateFilterThread.STATUS = "ACTIVO";
                                sampleRateThread = new SampleRateFilterThread(ticWatchRepository, e4BandRepository,
                                        eHealthBoardRepository, globalMonitoringViewModel, session_id);
                                sampleRateThread.start();

                                // E iniciamos el Fragment de monitorización
                                DevicesMonitoringFragment fragment = new DevicesMonitoringFragment(session_id,
                                        sessionResult);
                                FragmentManager fragmentManager = getSupportFragmentManager();
                                FragmentTransaction fragmentTransaction = fragmentManager.beginTransaction();
                                fragmentTransaction.setCustomAnimations(android.R.animator.fade_in,
                                        android.R.animator.fade_out);
                                fragmentTransaction.add(R.id.fragment_monitoring_show, fragment);
                                fragmentTransaction.commit();

                            } else {
                                // Manejo de error si no se pudo obtener una IP inicial
                                Toast.makeText(DevicesConnectionActivity.this,
                                        "Error: No se pudo asignar un nodo de streaming.", Toast.LENGTH_LONG).show();
                                DevicesConnectionActivity.crashed = true; // Marcar la app como crash para detener el
                                                                          // proceso
                                // Aquí NO INICIAMOS SampleRateFilterThread ni el fragment de monitorización
                            }
                        }
                    });

                    break;

                case 2: // Sesión finalizada correctamente
                    // Obtenemos el timestamp fin del result
                    String timestamp_fin_success = resultData.getString("result_time");
                    stopWatchAndThreads();
                    stopDBLocalSession(timestamp_fin_success);

                    // Mostramos resultados
                    Intent i_success = new Intent(DevicesConnectionActivity.this, SessionResultActivity.class);
                    i_success.putExtra("session_id", session_id);
                    startActivity(i_success);
                    // Destruimos el de conexiones para que no se pueda volver a él.
                    finish();

                    break;

                // Error al iniciar sesión
                case 400:
                    Toast.makeText(DevicesConnectionActivity.this, "Error al iniciar sesión. ¿Dispone de conexión?",
                            Toast.LENGTH_SHORT).show();
                    break;

                // Error al finalizar la sesión (corrupta)
                case 401:
                    String timestamp_fin_corrupt = resultData.getString("result_time");
                    stopWatchAndThreads();
                    stopDBLocalSession(timestamp_fin_corrupt);
                    Toast.makeText(DevicesConnectionActivity.this,
                            "Sesión emitida al servidor corrupta.\n Sincronícela de nuevo más tarde",
                            Toast.LENGTH_SHORT).show();
                    // Mostramos resultados
                    Intent i_corrupt = new Intent(DevicesConnectionActivity.this, SessionResultActivity.class);
                    i_corrupt.putExtra("session_id", session_id);
                    startActivity(i_corrupt);
                    finish();
                    break;

                // Caso para finalizar la sesión en modo sin conexión
                case 300:
                    // No hay acciones específicas definidas para este caso.
                    break;
            }
        }

    };

    private void getInitialStreamingNodeIp(@NonNull final Runnable onNodeIpReceived) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    // Primera llamada síncrona al gestor de nodos
                    Response<AuthApiService.NodeIpResponse> response = authApiService.getAvailableNodeIp().execute();
                    if (response.isSuccessful() && response.body() != null) {
                        String initialIp = response.body().ip; // <-- Correcto aquí (primera llamada)
                        // Comprobar la salud del nodo asignado inicialmente
                        if (isNodeHealthy(initialIp)) {
                            Constants.CURRENT_STREAMING_NODE_IP = initialIp;
                            Log.i("DevicesConnection", "Primera IP de nodo asignada: " + initialIp);
                        } else {
                            Log.e("DevicesConnection",
                                    "El nodo inicial asignado (" + initialIp + ") no está activo. Reintentando...");
                            // Si el primer nodo no está activo, intentamos pedir otro.
                            response = authApiService.getAvailableNodeIp().execute(); // Segunda llamada
                            if (response.isSuccessful() && response.body() != null) {
                                String secondAttemptIp = response.body().ip;
                                if (isNodeHealthy(secondAttemptIp)) {
                                    Constants.CURRENT_STREAMING_NODE_IP = secondAttemptIp;
                                    Log.i("DevicesConnection",
                                            "Segunda IP de nodo asignada y activa: " + secondAttemptIp);
                                } else {
                                    Log.e("DevicesConnection",
                                            "Ni la segunda IP asignada (" + secondAttemptIp + ") está activa.");
                                    Constants.CURRENT_STREAMING_NODE_IP = null;
                                }
                            } else {
                                Log.e("DevicesConnection", "Error al obtener segunda IP del gestor: "
                                        + response.code() + " " + response.message());
                                Constants.CURRENT_STREAMING_NODE_IP = null;
                            }
                        }
                    } else {
                        Log.e("DevicesConnection", "Error al obtener IP inicial del gestor: " + response.code()
                                + " " + response.message());
                        Constants.CURRENT_STREAMING_NODE_IP = null;
                    }
                } catch (IOException e) {
                    Log.e("DevicesConnection",
                            "Fallo de red al contactar al gestor por primera vez: " + e.getMessage());
                    Constants.CURRENT_STREAMING_NODE_IP = null;
                } catch (Exception e) {
                    Log.e("DevicesConnection", "Excepción al obtener IP inicial: " + e.getMessage());
                    Constants.CURRENT_STREAMING_NODE_IP = null;
                } finally {
                    // SIEMPRE, sin importar el resultado, postear el Runnable al hilo principal
                    new Handler(Looper.getMainLooper()).post(onNodeIpReceived);
                }
            }
        }).start();
    }

    // Método auxiliar para comprobar la salud del nodo
    private boolean isNodeHealthy(String nodeIp) {
        if (nodeIp == null || nodeIp.isEmpty()) {
            Log.e("NodeHealthCheck", "IP de nodo para health check es nula o vacía.");
            return false;
        }
        try {
            // Asumiendo que Constants.NODE_HEALTH_PATH es algo como "/health"
            String healthCheckUrl = "http://" + nodeIp + Constants.NODE_HEALTH_PATH;
            Response<Void> response = authApiService.checkNodeHealth(healthCheckUrl).execute();
            return response.isSuccessful();
        } catch (IOException e) {
            Log.e("NodeHealthCheck",
                    "Fallo de red en comprobación de salud inicial de " + nodeIp + ": " + e.getMessage());
            return false;
        } catch (Exception e) {
            Log.e("NodeHealthCheck",
                    "Excepción en comprobación de salud inicial de " + nodeIp + ": " + e.getMessage());
            return false;
        }
    }

    private void initDBLocalSession() {

        // Inicio la sesión
        sessionsRepository.insertSession(new SessionEntity(
                session_id, user_id, instant.toString(), instant.toString(), 0, e4Connected, ticwatchConnected,
                ehealthConnected, session_description, sync, false));

    }

    private void stopDBLocalSession(String timestamp_fin) {
        // Hacemos update de la sesión
        sessionsRepository.updateSession(new SessionEntity(
                session_id, user_id, instant.toString(), timestamp_fin,
                Constants.getTotalSecs(instant.toString(), timestamp_fin), e4Connected, ticwatchConnected,
                ehealthConnected, session_description, sync, DevicesConnectionActivity.crashed));

    }

    /**
     * Iniciamos la placa de salud
     * 
     * @author Domingo Lopez
     */
    void initEHeatlhBoard() {
        try {
            byte[] inicio = "S".getBytes();
            this.myOutStream.write(inicio);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * Paramos la recepción de datos de la placa de salud
     * 
     * @author Domingo Lopez
     */
    void stopEHealthBoard() {
        try {
            if (this.myOutStream != null) {
                byte[] parada = "N".getBytes();
                this.myOutStream.write(parada);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * Reseteamos los repositorios de los datos recibidos
     * 
     * @author Domingo Lopez
     */
    void resetRepositories() {

        this.ticWatchRepository.reset();
        this.e4BandRepository.reset();
        this.eHealthBoardRepository.reset();

    }

    /**
     * Para la emisión de datos del reloj Watch y de las hebras activas
     * 
     * @author Domingo Lopez
     */
    void stopWatchAndThreads() {

        String timeback1 = String.valueOf(System.currentTimeMillis());
        putDataMapRequestStop.getDataMap().putString("MONITORINGSTOP", timeback1);
        putDataReqStop = putDataMapRequestStop.asPutDataRequest();
        Task<DataItem> putDataTask2 = dataClient.putDataItem(putDataReqStop);
        putDataTask2.addOnCompleteListener(new OnCompleteListener<DataItem>() {
            @Override
            public void onComplete(@NonNull Task<DataItem> task) {
                Log.i("INFOTASK", "PUESTO VALOR STOP MONITORING EN DATACLIENT");
            }
        });
        SampleRateFilterThread.STATUS = "INACTIVO";
        EhealthBoardThread.STATUS = "INACTIVO";

    }

    /**
     * Método de la empática dirigido por evento que se llama cuando se recibe un
     * cambio de estado de la pulsera
     * 
     * @author Domingo Lopez
     * @param status
     */
    @Override
    public void didUpdateStatus(EmpaStatus status) {
        // DeviceManager Ready
        if (status == EmpaStatus.READY) {
            // Comienza el Escanero
            try {
                deviceManager.startScanning();
                // Conexión establecida
            } catch (Exception e) {
                new AlertDialog.Builder(this)
                        .setTitle("Error")
                        .setIcon(android.R.drawable.ic_dialog_info)
                        .setCancelable(true)
                        .setMessage(
                                "Device manager is unable to download label file and may reject connecting to your device.")
                        .setPositiveButton("Ok", new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int which) {
                                dialog.dismiss();
                            }
                        })
                        .show();
            }
            // Si se establece la conexión
        } else if (status == EmpaStatus.CONNECTED) {
            this.runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    btnE4BandConnect.setText("Conectado");
                    btnE4BandConnect.setBackgroundColor(
                            btnE4BandConnect.getContext().getResources().getColor(R.color.e4connected));
                    e4Connected = true;
                }
            });

            // Se desconecta el device manager
        } else if (status == EmpaStatus.DISCONNECTED) {
            Log.i("ESTADO:", status.toString());
            this.runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    btnE4BandConnect.setText("Desconectado");
                    btnE4BandConnect.setBackgroundColor(
                            btnE4BandConnect.getContext().getResources().getColor(R.color.e4disconnected));

                    e4Connected = false;
                }
            });

        }
    }

    @Override
    public void didEstablishConnection() {

    }

    @Override
    public void didUpdateSensorStatus(int status, EmpaSensorType type) {

    }

    /**
     * Método que checkea si nuestro dispositivo se puede conectar con la pulsera
     * empática
     * 
     * @author Domingo Lopez
     * @param bluetoothDevice
     * @param deviceLabel
     * @param rssi
     * @param allowed
     */
    @Override
    public void didDiscoverDevice(EmpaticaDevice bluetoothDevice, String deviceLabel, int rssi, boolean allowed) {
        if (allowed) {
            // Paramos de escanear
            deviceManager.stopScanning();
            try {
                // Nos conectamos a la empatica
                deviceManager.connectDevice(bluetoothDevice);
            } catch (ConnectionNotAllowedException e) {
                Log.i("ERROR", "Connection:" + e.toString());
            }
        }
    }

    @Override
    public void didFailedScanning(int errorCode) {
        Log.i("ENTRO FAILED SCANNING", "");
    }

    @Override
    public void didRequestEnableBluetooth() {
        // Request the user to enable Bluetooth
        Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
        startActivityForResult(enableBtIntent, REQUEST_ENABLE_BT);
    }

    @Override
    public void bluetoothStateChanged() {

    }

    @Override
    public void didUpdateOnWristStatus(int status) {

    }

    /**
     * Método que se lanza tras pedir los permisos Bluetooth
     * 
     * @author Domingo Lopez
     * @param requestCode
     * @param resultCode
     * @param data
     */
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQUEST_ENABLE_BT && resultCode == Activity.RESULT_CANCELED) {
            finish();
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
        initEmpaticaDeviceManager();
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (deviceManager != null) {
            deviceManager.disconnect();
        }

        // Quitamos el Listener de las capabilities del watch
        Wearable.getCapabilityClient(this).removeListener(this, Constants.CAPABILITY_WEAR_APP);
        Wearable.getDataClient(this).removeListener(this);
    }

    /**
     * Al destruir la aplicación borramos el rastro que hayamos podido dejar para no
     * crear fugas de memoria
     * 
     * @author Domingo Lopez
     */
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (deviceManager != null) {
            Log.d("E4Service", "Disconnecting");
            deviceManager.disconnect();
        }
        SampleRateFilterThread.STATUS = "INACTIVO";
        EhealthBoardThread.STATUS = "INACTIVO";

        if (this.ehealthConnected)
            this.stopEHealthBoard();

        if (this.bluetoothSocket != null) {
            try {
                this.bluetoothSocket.close();
            } catch (IOException e) {
                e.printStackTrace();
            }

        }

        stopWatchAndThreads();

        // NO BORRAMOS LA SESIÓN LOCAL ALMACENADA.
        /*
         * if(Constants.CONNECTION_MODE=="STREAMING"){
         * this.sessionsRepository.deleteByIdSession(this.id_session_local);
         * this.e4BandRepository.deleteByIdSession(this.id_session_local);
         * this.ticWatchRepository.deleteByIdSession(this.id_session_local);
         * this.eHealthBoardRepository.deleteByIdSession(this.id_session_local);
         * }
         */

    }

    /**
     * Método lanzado cada vez se cambia las "capabilities" que tienen los
     * nodos/dispositivos Wear cercanos mientras estamos escaneando por ellos
     * 
     * @author Domingo Lopez
     * @param capabilityInfo
     */
    @Override
    public void onCapabilityChanged(@NonNull CapabilityInfo capabilityInfo) {

        this.wearNodesWithApp = capabilityInfo.getNodes();

        findAllWearDevices();
        verifyNodeAndWaitForMonitoring();
    }

    /**
     * Método que busca dispositivos con nuestra app instalada
     * 
     * @author Domingo Lopez
     */
    private void findWearDevicesWithApp() {

        Task<CapabilityInfo> capabilityInfoTask;
        capabilityInfoTask = Wearable.getCapabilityClient(this)
                .getCapability(Constants.CAPABILITY_WEAR_APP, CapabilityClient.FILTER_ALL);

        capabilityInfoTask.addOnCompleteListener(new OnCompleteListener<CapabilityInfo>() {
            @Override
            public void onComplete(Task<CapabilityInfo> task) {

                if (task.isSuccessful()) {

                    CapabilityInfo capabilityInfo = task.getResult();
                    wearNodesWithApp = capabilityInfo.getNodes();

                    Log.d("INFO", "Capable Nodes: " + wearNodesWithApp);

                    verifyNodeAndWaitForMonitoring();

                } else {
                    Log.d("ERROR", "Capability request failed to return any results.");
                    btnWatchConnect.setBackgroundColor(
                            btnWatchConnect.getContext().getResources().getColor(R.color.e4disconnected));
                    btnWatchConnect.setText("Desconectado");
                    ticwatchConnected = false;
                }
            }
        });
    }

    /**
     * Método que busca dispositivos WearOS sin importar si tienen o no nuestra app
     * instalada
     * 
     * @author Domingo Lopez
     */
    private void findAllWearDevices() {

        Task<List<Node>> NodeListTask = Wearable.getNodeClient(this).getConnectedNodes();

        NodeListTask.addOnCompleteListener(new OnCompleteListener<List<Node>>() {
            @Override
            public void onComplete(Task<List<Node>> task) {

                if (task.isSuccessful()) {
                    Log.d("INFO", "Node request succeeded.");
                    allConnectedNodes = task.getResult();

                } else {
                    Log.d("ERROR", "Node request failed to return any results.");
                    btnWatchConnect.setBackgroundColor(
                            btnWatchConnect.getContext().getResources().getColor(R.color.e4disconnected));
                    btnWatchConnect.setText("Desconectado");

                    ticwatchConnected = false;
                }

                verifyNodeAndWaitForMonitoring();
            }
        });
    }

    /**
     * Una vez escaneados los dispositivos WearOS, si tienen nuestra app nos
     * podremos conectar.
     * Este método checkea si hemos detectado dispositivos y si tienen nuestra app
     * instalada. Si es correcto,
     * setea la vista y anota el dispositivo como conectado.
     * 
     * @author Domingo Lopez
     */
    private void verifyNodeAndWaitForMonitoring() {

        if ((this.wearNodesWithApp == null) || (this.allConnectedNodes == null)) {
            Log.d("ERROR", "Esperando resultados de nodos conectados con la app");
        } else if (this.allConnectedNodes.isEmpty()) {
            Log.d("INFO", "No hay nodos conectados");
        } else if (this.wearNodesWithApp.isEmpty()) {
            Log.d("INFO", "El dispositivo WearOs no dispone de la app necesaria");
        } else if (this.wearNodesWithApp.size() < this.allConnectedNodes.size()) {

            Log.i("INFO", "Algún nodo conectado. Esperando inicio de la monitorización...");
            this.btnWatchConnect.setText("Conectado");
            this.btnWatchConnect
                    .setBackgroundColor(this.btnWatchConnect.getContext().getResources().getColor(R.color.e4connected));

            ticwatchConnected = true;

        } else {

            Log.i("INFO", "Todos los nodos conectados. Esperando inicio de la monitorización...");
            this.btnWatchConnect.setText("Conectado");
            this.btnWatchConnect
                    .setBackgroundColor(this.btnWatchConnect.getContext().getResources().getColor(R.color.e4connected));

            ticwatchConnected = true;

        }
    }

    /**
     * Método que es llamado cada vez que lee en el DATAMAP de la api de Google,
     * haciendo uso de DataClient. El objetivo
     * es sincronizar los datos entre el reloj y la app
     * 
     * @author Domingo Lopez
     * @param dataEventBuffer
     */
    @Override
    public void onDataChanged(@NonNull DataEventBuffer dataEventBuffer) {

        for (DataEvent event : dataEventBuffer) {
            if (event.getType() == DataEvent.TYPE_CHANGED) {
                // DataItem changed
                DataItem item = event.getDataItem();
                if (item.getUri().getPath().compareTo("/ACC") == 0) {
                    DataMap dataMap = DataMapItem.fromDataItem(item).getDataMap();
                    this.ticWatchRepository.setAccx(dataMap.getFloat("ACCX"));
                    this.ticWatchRepository.setAccy(dataMap.getFloat("ACCY"));
                    this.ticWatchRepository.setAccz(dataMap.getFloat("ACCZ"));

                } else if (item.getUri().getPath().compareTo("/ACCL") == 0) {
                    DataMap dataMap = DataMapItem.fromDataItem(item).getDataMap();
                    this.ticWatchRepository.setAcclx(dataMap.getFloat("ACCLX"));
                    this.ticWatchRepository.setAccly(dataMap.getFloat("ACCLY"));
                    this.ticWatchRepository.setAcclz(dataMap.getFloat("ACCLZ"));
                } else if (item.getUri().getPath().compareTo("/GIR") == 0) {
                    DataMap dataMap = DataMapItem.fromDataItem(item).getDataMap();
                    this.ticWatchRepository.setGirx(dataMap.getFloat("GIRX"));
                    this.ticWatchRepository.setGiry(dataMap.getFloat("GIRY"));
                    this.ticWatchRepository.setGirz(dataMap.getFloat("GIRZ"));
                } else if (item.getUri().getPath().compareTo("/HRPPG") == 0) {
                    DataMap dataMap = DataMapItem.fromDataItem(item).getDataMap();
                    this.ticWatchRepository.setHrppg(dataMap.getFloat("HRPPG"));
                } else if (item.getUri().getPath().compareTo("/STEP") == 0) {
                    DataMap dataMap = DataMapItem.fromDataItem(item).getDataMap();
                    this.ticWatchRepository.setStep(dataMap.getInt("STEP"));
                }
            } else if (event.getType() == DataEvent.TYPE_DELETED) {
                // DataItem deleted
            }
        }
    }

    /**
     * Método lanzado al pulsar el botón de ir hacia atras.
     * Limpiar basura para evitar fugas de memoria
     * 
     * @author Domingo Lopez
     */
    @Override
    public void onBackPressed() {
        if (this.ehealthConnected)
            this.stopEHealthBoard();

        if (this.bluetoothSocket != null) {
            try {
                this.bluetoothSocket.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        finish();
    }
}