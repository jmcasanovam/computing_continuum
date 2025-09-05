package com.hdrescuer.hdrescuer.ui.ui.devicesconnection.services;

import android.app.IntentService;
import android.content.Intent;
import android.util.Log;

import com.hdrescuer.hdrescuer.common.Constants;
import com.hdrescuer.hdrescuer.retrofit.AuthApiService;
import com.hdrescuer.hdrescuer.retrofit.AuthConectionClient;
import com.hdrescuer.hdrescuer.retrofit.request.RequestSendData;
import com.hdrescuer.hdrescuer.ui.ui.devicesconnection.DevicesConnectionActivity; // Para la bandera 'crashed'


import java.io.IOException;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * IntentService que recibe los datos a mandar al servidor y los manda,
 * incluyendo lógica para gestionar la asignación dinámica de nodos.
 * @author Domingo Lopez
 */
public class RestSampleRateService extends IntentService {

    private static final String ACTION_SEND = "ACTION_SEND";

    AuthApiService authApiService;
    AuthConectionClient authConnectionClient;

    public RestSampleRateService() {
        super("RestSampleRateService");
        this.authConnectionClient = AuthConectionClient.getInstance();
        this.authApiService = this.authConnectionClient.getAuthApiService();
    }

    @Override
    protected void onHandleIntent(Intent intent) {
        if (intent == null || !intent.getAction().equals(ACTION_SEND)) {
            Log.w("RestSampleRateService", "Intent nulo o acción incorrecta recibida.");
            return;
        }

        String currentNodeIp = Constants.CURRENT_STREAMING_NODE_IP;
        String activeNodeIp = null; // IP que usaremos para el envío en este ciclo

        // --- Lógica de Comprobación y Re-asignación de Nodo ---
        // Siempre intentamos validar el nodo actual. Si es nulo o falla, solicitamos uno nuevo.
        if (currentNodeIp == null) {
            Log.w("RestSampleRateService", "No hay nodo asignado. Solicitando uno nuevo...");
            activeNodeIp = getAndValidateNewNodeIp(); // Intentamos obtener y validar un nodo
        } else if (DevicesConnectionActivity.crashed) {
            Log.w("RestSampleRateService", "Envío anterior falló. Validando nodo actual o solicitando uno nuevo.");
            // Si el anterior envío falló, intentamos revalidar el actual.
            // Si no está activo, intentamos pedir uno nuevo.
            if (isNodeActive(currentNodeIp)) {
                activeNodeIp = currentNodeIp;
                Log.i("RestSampleRateService", "Nodo actual " + currentNodeIp + " se ha recuperado/validado.");
                DevicesConnectionActivity.crashed = false; // Resetear la bandera si se recupera
            } else {
                Log.w("RestSampleRateService", "Nodo actual " + currentNodeIp + " está inactivo. Solicitando uno nuevo.");
                activeNodeIp = getAndValidateNewNodeIp();
            }
        } else {
            // Tenemos una IP asignada y el último envío no falló.
            // Aún así, validamos proactivamente su salud.
            Log.d("RestSampleRateService", "Validando salud del nodo asignado: " + currentNodeIp);
            if (isNodeActive(currentNodeIp)) {
                activeNodeIp = currentNodeIp;
            } else {
                Log.w("RestSampleRateService", "Nodo " + currentNodeIp + " se volvió inactivo. Solicitando uno nuevo.");
                activeNodeIp = getAndValidateNewNodeIp(); // Si el actual falla, pedimos uno nuevo
            }
        }


        if (activeNodeIp == null) {
            Log.e("RestSampleRateService", "FALLO CRÍTICO: No se pudo obtener/validar un nodo de streaming. No se enviarán datos.");
            DevicesConnectionActivity.crashed = true; // Asegurar que la bandera de fallo esté activa
            return; // Salir, no hay nodo válido para enviar
        }

        // A este punto, 'activeNodeIp' debe ser la IP del nodo activo y validado
        // Construimos la URL completa para el envío de datos
        final String finalActiveNodeIp = activeNodeIp;
        String dataUploadUrl = "http://" + finalActiveNodeIp + Constants.NODE_DATA_UPLOAD_PATH;

        // Recogemos todos los parámetros y creamos el objeto a mandar
        RequestSendData newRequest = new RequestSendData(
            String.valueOf(intent.getIntExtra("session_id", 0)),
            intent.getStringExtra("timestamp"),
            intent.getStringExtra("tic_hrppg"),
            intent.getStringExtra("tic_hrppgraw"),
            intent.getStringExtra("tic_step"),
            intent.getStringExtra("tic_accx"),
            intent.getStringExtra("tic_accy"),
            intent.getStringExtra("tic_accz"),
            intent.getStringExtra("tic_acclx"),
            intent.getStringExtra("tic_accly"),
            intent.getStringExtra("tic_acclz"),
            intent.getStringExtra("tic_girx"),
            intent.getStringExtra("tic_giry"),
            intent.getStringExtra("tic_girz"),

            intent.getStringExtra("e4_accx"),
            intent.getStringExtra("e4_accy"),
            intent.getStringExtra("e4_accz"),
            intent.getStringExtra("e4_bvp"),
            intent.getStringExtra("e4_hr"),
            intent.getStringExtra("e4_gsr"),
            intent.getStringExtra("e4_ibi"),
            intent.getStringExtra("e4_temp"),

            intent.getStringExtra("ehb_bpm"),
            intent.getStringExtra("ehb_o2"),
            intent.getStringExtra("ehb_air"),
            intent.getBooleanExtra("e4Connected",false),
            intent.getBooleanExtra("ticWatchConnected",false),
            intent.getBooleanExtra("eHealthBoardConnected",false)
        );

        // Realizamos la llamada al servidor utilizando la URL dinámica
        newRequest.setUserId("user_app");
        Call<String> call = authApiService.setUserData(dataUploadUrl, newRequest);
        call.enqueue(new Callback<String>() {
            @Override
            public void onResponse(Call<String> call, Response<String> response) {
                if(response.isSuccessful()){
                    Log.i("RestSampleRateService", "Datos enviados correctamente al nodo: " + finalActiveNodeIp);
                    DevicesConnectionActivity.crashed = false; // Restablecer la bandera si el envío fue exitoso
                } else {
                    Log.e("RestSampleRateService", "ERROR " + response.code() + " en el envío de datos al nodo " + finalActiveNodeIp + ": " + response.message());
                    DevicesConnectionActivity.crashed = true; // Marcar como fallido para re-validar/re-asignar en el siguiente intento
                }
            }

            @Override
            public void onFailure(Call<String> call, Throwable t) {
                Log.e("RestSampleRateService", "FALLO DE RED al enviar datos al nodo " + finalActiveNodeIp + ": " + t.getMessage());
                DevicesConnectionActivity.crashed = true; // Marcar como fallido para re-validar/re-asignar
            }
        });
    }

    /**
     * Intenta obtener una nueva IP del gestor y la valida.
     * Realiza llamadas síncronas (aceptable en IntentService).
     * @return La IP de un nodo activo, o null si no se pudo obtener/validar.
     */
    private String getAndValidateNewNodeIp() {
        try {
            Log.d("NodeManager", "Solicitando nueva IP del gestor...");
            Response<AuthApiService.NodeIpResponse> response = authApiService.getAvailableNodeIp().execute();
            if (response.isSuccessful() && response.body() != null) {
                String newIp = response.body().ip;
                Log.d("NodeManager", "Gestor asignó la IP: " + newIp);
                if (isNodeActive(newIp)) {
                    Log.d("NodeHealthCheck", "Nueva IP " + newIp + " está activa y validada.");
                    return newIp;
                } else {
                    Log.w("NodeHealthCheck", "La IP asignada " + newIp + " no está activa.");
                    return null; // El nodo asignado no es válido
                }
            } else {
                Log.e("NodeManager", "Error al obtener IP del gestor: " + response.code() + " " + response.message());
                return null;
            }
        } catch (IOException e) {
            Log.e("NodeManager", "Fallo de red al contactar al gestor: " + e.getMessage());
            return null;
        } catch (Exception e) {
            Log.e("NodeManager", "Excepción al obtener IP del gestor: " + e.getMessage());
            return null;
        }
    }

    /**
     * Realiza un health check síncrono a un nodo dado.
     * @param nodeIp La IP del nodo a comprobar.
     * @return true si el nodo responde con un 2xx, false en caso contrario (incluyendo fallos de red).
     */
    private boolean isNodeActive(String nodeIp) {
        if (nodeIp == null || nodeIp.isEmpty()) {
            Log.e("NodeHealthCheck", "IP de nodo para health check es nula o vacía.");
            return false;
        }
        try {
            String healthCheckUrl = "http://" + nodeIp + Constants.NODE_HEALTH_PATH;
            Response<Void> response = authApiService.checkNodeHealth(healthCheckUrl).execute();
            return response.isSuccessful();
        } catch (IOException e) {
            Log.e("NodeHealthCheck", "Fallo de red al comprobar salud de " + nodeIp + ": " + e.getMessage());
            return false;
        } catch (Exception e) {
            Log.e("NodeHealthCheck", "Excepción al comprobar salud de " + nodeIp + ": " + e.getMessage());
            return false;
        }
    }
}