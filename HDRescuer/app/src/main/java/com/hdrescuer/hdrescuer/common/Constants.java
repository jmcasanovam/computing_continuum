package com.hdrescuer.hdrescuer.common;

import java.time.Duration;
import java.time.Instant;

/**
 * Clase de variables y métodos comunes entre las distintas clases. Cosas que puedan ser usadas por más de una instancia
 * @author Domingo Lopez
 */
public class Constants {


    public static final String DATA_RESCUER_API_GATEWAY= "http://192.168.1.141:8080/";

    // public static final String BASE_URL_MANAGER = "http://192.168.1.141:8000";
    public static final String BASE_URL_MANAGER = "http://192.168.1.141:30001";

    // 30001/api/available-node
    public static String CURRENT_STREAMING_NODE_IP = null;

    // Rutas relativas para los endpoints de los nodos de datos
    public static final String NODE_HEALTH_PATH = ":30080/health"; // Endpoint para comprobar la salud del nodo
    public static final String NODE_DATA_UPLOAD_PATH = ":30080/api/datarecovery/data"; // Endpoint para enviar los datos de sensores

    //API E4BAND
    public static final String EMPATICA_API_KEY = "6eeeec064b8f44b2b7f879f68ea34a78";

    //CAPABILITIES TO DETECT EACH OTHER (PHONE AND WATCH)
    //Si se cambia debe cambiarse también en /res/values/wear.xml
    public static final String CAPABILITY_WEAR_APP = "verify_remote_example_wear_app";

    //SAMPLE RATE
    public static int SAMPLE_RATE = 200;

    //VARIABLE QUE DEFINE SI ESTAMOS EN MODO NO CONEXIÓN
    public static String CONNECTION_MODE = "";

    //VARIABLE QUE DEFINE SI TENEMOS CONEXIÓN O NO
    public static String CONNECTION_UP ="NO";


    /**
     * Método que calcula las horas, minutos y segundos de un entero de segundos
     * @author Domingo Lopez
     * @param secs
     * @return String
     */
    public static String getHMS(long secs){

        long hours = secs / 3600;
        long minutes = (secs % 3600) / 60;
        long seconds = secs % 60;

        String chain = String.valueOf(hours)+"h:"+ String.valueOf(minutes) +"m:"+ String.valueOf(seconds)+"s";

        return chain;

    }

    /**
     * Método que devuelve el total de segundos entre dos instantes de tiempo pasados como Strings
     * @param timestamp_ini
     * @param timestamp_fin
     * @return
     */
    public static long getTotalSecs(String timestamp_ini, String timestamp_fin){

        Instant timestampini = Instant.parse(timestamp_ini);
        Instant timestampfin = Instant.parse(timestamp_fin);

        Duration res = Duration.between(timestampini,timestampfin);
        long seconds = res.getSeconds();

        return seconds;
    }

}
