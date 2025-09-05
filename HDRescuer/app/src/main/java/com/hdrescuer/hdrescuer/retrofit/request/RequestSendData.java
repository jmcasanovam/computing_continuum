package com.hdrescuer.hdrescuer.retrofit.request;

import java.io.Serializable;
import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;

/**
 * Clase RequesSendData serializable. Representa el envío de datos de un paquete
 * de datos hacia el servidor
 * 
 * @author Domingo López
 */
public class RequestSendData implements Serializable {

    @SerializedName("session_id")
    @Expose
    private String session_id;
    @SerializedName("timeStamp")
    @Expose
    private String timeStamp;
    @SerializedName("tic_hrppg")
    @Expose
    private String ticHrppg;
    @SerializedName("tic_hrppgraw")
    @Expose
    private String ticHrppgraw;
    @SerializedName("tic_step")
    @Expose
    private String ticStep;
    @SerializedName("tic_accx")
    @Expose
    private String ticAccx;
    @SerializedName("tic_accy")
    @Expose
    private String ticAccy;
    @SerializedName("tic_accz")
    @Expose
    private String ticAccz;
    @SerializedName("tic_acclx")
    @Expose
    private String ticAcclx;
    @SerializedName("tic_accly")
    @Expose
    private String ticAccly;
    @SerializedName("tic_acclz")
    @Expose
    private String ticAcclz;
    @SerializedName("tic_girx")
    @Expose
    private String ticGirx;
    @SerializedName("tic_giry")
    @Expose
    private String ticGiry;
    @SerializedName("tic_girz")
    @Expose
    private String ticGirz;
    @SerializedName("e4_accx")
    @Expose
    private String e4Accx;
    @SerializedName("e4_accy")
    @Expose
    private String e4Accy;
    @SerializedName("e4_accz")
    @Expose
    private String e4Accz;
    @SerializedName("e4_bvp")
    @Expose
    private String e4Bvp;
    @SerializedName("e4_hr")
    @Expose
    private String e4Hr;
    @SerializedName("e4_gsr")
    @Expose
    private String e4Gsr;
    @SerializedName("e4_ibi")
    @Expose
    private String e4Ibi;
    @SerializedName("e4_temp")
    @Expose
    private String e4Temp;
    @SerializedName("ehb_bpm")
    @Expose
    private String ehb_bpm;
    @SerializedName("ehb_o2")
    @Expose
    private String ehb_o2;
    @SerializedName("ehb_air")
    @Expose
    private String ehb_air;
    @SerializedName("e4connected")
    @Expose
    private boolean e4connected;
    @SerializedName("ticwatchconnected")
    @Expose
    private boolean ticwatchconnected;
    @SerializedName("ehealthboardconnected")
    @Expose
    private boolean ehealthboardconnected;
    @SerializedName("user_id")
    @Expose
    private String user_id;

    private final static long serialVersionUID = 4226884065588354866L;

    /**
     * Constructor vacío
     * 
     * @author Domingo Lopez
     * 
     */
    public RequestSendData() {
    }

    /**
     * Cosntructor con parámetros
     * 
     * @author Domingo Lopez
     * @param session_id
     * @param timeStamp
     * @param ticHrppg
     * @param ticHrppgraw
     * @param ticStep
     * @param ticAccx
     * @param ticAccy
     * @param ticAccz
     * @param ticAcclx
     * @param ticAccly
     * @param ticAcclz
     * @param ticGirx
     * @param ticGiry
     * @param ticGirz
     * @param e4Accx
     * @param e4Accy
     * @param e4Accz
     * @param e4Bvp
     * @param e4Hr
     * @param e4Gsr
     * @param e4Ibi
     * @param e4Temp
     * @param ehb_bmp
     * @param ehb_o2
     * @param ehb_air
     * @param e4connected
     * @param ticwatchconnected
     * @param ehealthboardconnected
     */
    public RequestSendData(String session_id, String timeStamp, String ticHrppg, String ticHrppgraw, String ticStep,
            String ticAccx, String ticAccy, String ticAccz, String ticAcclx, String ticAccly, String ticAcclz,
            String ticGirx, String ticGiry, String ticGirz, String e4Accx, String e4Accy, String e4Accz, String e4Bvp,
            String e4Hr, String e4Gsr, String e4Ibi, String e4Temp, String ehb_bmp, String ehb_o2, String ehb_air,
            boolean e4connected, boolean ticwatchconnected, boolean ehealthboardconnected) {
        super();
        this.session_id = session_id;
        this.timeStamp = timeStamp;
        this.ticHrppg = ticHrppg;
        this.ticHrppgraw = ticHrppgraw;
        this.ticStep = ticStep;
        this.ticAccx = ticAccx;
        this.ticAccy = ticAccy;
        this.ticAccz = ticAccz;
        this.ticAcclx = ticAcclx;
        this.ticAccly = ticAccly;
        this.ticAcclz = ticAcclz;
        this.ticGirx = ticGirx;
        this.ticGiry = ticGiry;
        this.ticGirz = ticGirz;
        this.e4Accx = e4Accx;
        this.e4Accy = e4Accy;
        this.e4Accz = e4Accz;
        this.e4Bvp = e4Bvp;
        this.e4Hr = e4Hr;
        this.e4Gsr = e4Gsr;
        this.e4Ibi = e4Ibi;
        this.e4Temp = e4Temp;
        this.ehb_bpm = ehb_bmp;
        this.ehb_o2 = ehb_o2;
        this.ehb_air = ehb_air;
        this.e4connected = e4connected;
        this.ticwatchconnected = ticwatchconnected;
        this.ehealthboardconnected = ehealthboardconnected;
    }

    public void setUserId(String user_id) {
        this.user_id = user_id;
    }

    public String getUserId() {
        return user_id;
    }

    public String getSession_id() {
        return String.valueOf(session_id);
    }

    public void setSession_id(int session_id) {
        this.session_id = String.valueOf(session_id);
    }

    public String getTimeStamp() {
        return timeStamp;
    }

    public void setTimeStamp(String timeStamp) {
        this.timeStamp = timeStamp;
    }

    public String getTicHrppg() {
        return ticHrppg;
    }

    public void setTicHrppg(String ticHrppg) {
        this.ticHrppg = ticHrppg;
    }

    public String getTicHrppgraw() {
        return ticHrppgraw;
    }

    public void setTicHrppgraw(String ticHrppgraw) {
        this.ticHrppgraw = ticHrppgraw;
    }

    public String getTicStep() {
        return ticStep;
    }

    public void setTicStep(String ticStep) {
        this.ticStep = ticStep;
    }

    public String getTicAccx() {
        return ticAccx;
    }

    public void setTicAccx(String ticAccx) {
        this.ticAccx = ticAccx;
    }

    public String getTicAccy() {
        return ticAccy;
    }

    public void setTicAccy(String ticAccy) {
        this.ticAccy = ticAccy;
    }

    public String getTicAccz() {
        return ticAccz;
    }

    public void setTicAccz(String ticAccz) {
        this.ticAccz = ticAccz;
    }

    public String getTicAcclx() {
        return ticAcclx;
    }

    public void setTicAcclx(String ticAcclx) {
        this.ticAcclx = ticAcclx;
    }

    public String getTicAccly() {
        return ticAccly;
    }

    public void setTicAccly(String ticAccly) {
        this.ticAccly = ticAccly;
    }

    public String getTicAcclz() {
        return ticAcclz;
    }

    public void setTicAcclz(String ticAcclz) {
        this.ticAcclz = ticAcclz;
    }

    public String getTicGirx() {
        return ticGirx;
    }

    public void setTicGirx(String ticGirx) {
        this.ticGirx = ticGirx;
    }

    public String getTicGiry() {
        return ticGiry;
    }

    public void setTicGiry(String ticGiry) {
        this.ticGiry = ticGiry;
    }

    public String getTicGirz() {
        return ticGirz;
    }

    public void setTicGirz(String ticGirz) {
        this.ticGirz = ticGirz;
    }

    public String getE4Accx() {
        return e4Accx;
    }

    public void setE4Accx(String e4Accx) {
        this.e4Accx = e4Accx;
    }

    public String getE4Accy() {
        return e4Accy;
    }

    public void setE4Accy(String e4Accy) {
        this.e4Accy = e4Accy;
    }

    public String getE4Accz() {
        return e4Accz;
    }

    public void setE4Accz(String e4Accz) {
        this.e4Accz = e4Accz;
    }

    public String getE4Bvp() {
        return e4Bvp;
    }

    public void setE4Bvp(String e4Bvp) {
        this.e4Bvp = e4Bvp;
    }

    public String getE4Hr() {
        return e4Hr;
    }

    public void setE4Hr(String e4Hr) {
        this.e4Hr = e4Hr;
    }

    public String getE4Gsr() {
        return e4Gsr;
    }

    public void setE4Gsr(String e4Gsr) {
        this.e4Gsr = e4Gsr;
    }

    public String getE4Ibi() {
        return e4Ibi;
    }

    public void setE4Ibi(String e4Ibi) {
        this.e4Ibi = e4Ibi;
    }

    public String getE4Temp() {
        return e4Temp;
    }

    public void setE4Temp(String e4Temp) {
        this.e4Temp = e4Temp;
    }

    public String getEhb_bpm() {
        return ehb_bpm;
    }

    public void setEhb_bpm(String ehb_bpm) {
        this.ehb_bpm = ehb_bpm;
    }

    public String getEhb_o2() {
        return ehb_o2;
    }

    public void setEhb_o2(String ehb_o2) {
        this.ehb_o2 = ehb_o2;
    }

    public String getEhb_air() {
        return ehb_air;
    }

    public void setEhb_air(String ehb_air) {
        this.ehb_air = ehb_air;
    }

    public boolean isE4connected() {
        return e4connected;
    }

    public void setE4connected(boolean e4connected) {
        this.e4connected = e4connected;
    }

    public boolean isTicwatchconnected() {
        return ticwatchconnected;
    }

    public void setTicwatchconnected(boolean ticwatchconnected) {
        this.ticwatchconnected = ticwatchconnected;
    }

    public boolean isEhealthboardconnected() {
        return ehealthboardconnected;
    }

    public void setEhealthboardconnected(boolean ehealthboardconnected) {
        this.ehealthboardconnected = ehealthboardconnected;
    }
}
