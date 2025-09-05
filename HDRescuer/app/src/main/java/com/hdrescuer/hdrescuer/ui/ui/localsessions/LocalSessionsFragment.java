package com.hdrescuer.hdrescuer.ui.ui.localsessions;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.ResultReceiver;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.fragment.app.Fragment;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModelProvider;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.hdrescuer.hdrescuer.R;
import com.hdrescuer.hdrescuer.common.Constants;
import com.hdrescuer.hdrescuer.common.MyApp;
import com.hdrescuer.hdrescuer.common.OnSimpleDialogClick;
import com.hdrescuer.hdrescuer.common.SimpleDialogFragment;
import com.hdrescuer.hdrescuer.data.PatientListViewModel;
import com.hdrescuer.hdrescuer.data.SessionsListViewModel;
import com.hdrescuer.hdrescuer.db.entity.SessionEntity;
import com.hdrescuer.hdrescuer.retrofit.response.User;
import com.hdrescuer.hdrescuer.ui.ui.charts.SessionResultActivity;
import com.hdrescuer.hdrescuer.ui.ui.localsessions.services.UploadSessionService;
import com.hdrescuer.hdrescuer.ui.ui.patients.ListItemClickListener;

import java.util.HashMap;
import java.util.List;
import java.util.Map;


public class LocalSessionsFragment extends Fragment implements ListItemClickListener, View.OnClickListener {

    // TODO: Customize parameter argument names
    private static final String ARG_COLUMN_COUNT = "column-count";
    // TODO: Customize parameters
    private int mColumnCount = 1;

    RecyclerView recyclerView;
    MySessionsRecyclerViewAdapter adapter;
    List<SessionEntity> sessionList;
    List<User> users;
    SessionsListViewModel sessionsListViewModel;
    PatientListViewModel patientListViewModel;

    public Map<String, Integer> usuarios_predictivo = new HashMap<String,Integer>();

    boolean alreadyCreated = false;

    int position_selected;
    int user_selected;


    public LocalSessionsFragment() {

    }


    @SuppressWarnings("unused")
    public static LocalSessionsFragment newInstance(int columnCount) {
        LocalSessionsFragment fragment = new LocalSessionsFragment();
        Bundle args = new Bundle();
        args.putInt(ARG_COLUMN_COUNT, columnCount);
        fragment.setArguments(args);
        return fragment;
    }


    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (getArguments() != null) {
            mColumnCount = getArguments().getInt(ARG_COLUMN_COUNT);
        }


        //Obtenemos ViewModel de las sesiones
        this.sessionsListViewModel = new ViewModelProvider(requireActivity()).get(SessionsListViewModel.class);

        //Obtenemos viewmodel de los usuarios descargados
        this.patientListViewModel = new ViewModelProvider(requireActivity()).get(PatientListViewModel.class);

        alreadyCreated = true;

    }


    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {


        View view = inflater.inflate(R.layout.fragment_sessions_list, container, false);
        Context context = view.getContext();
        this.recyclerView = view.findViewById(R.id.list_sessions);
        this.recyclerView.setLayoutManager(new LinearLayoutManager(context));

        this.users = this.patientListViewModel.getPatients().getValue();
        setUsersAElegir();

        this.adapter = new MySessionsRecyclerViewAdapter(
                getActivity(),
                this.sessionList,
                this.users,
                this
        );
        this.recyclerView.setAdapter(adapter);


        findViews(view);
        loadSessionsData();

        return view;
    }

    void setUsersAElegir(){
        if(this.users != null){
            for(int i = 0; i< this.users.size(); i++){
                this.usuarios_predictivo.put(this.users.get(i).getLastname()+", "+this.users.get(i).getUsername(), this.users.get(i).getUser_id());
            }
        }

    }


    @Override
    public void onResume() {
        super.onResume();
        if(!alreadyCreated){
/*
            refreshSessions();
*/
        }
        alreadyCreated = false;
    }


/*
    private void refreshSessions() {
        this.sessionsListViewModel.refreshSessions();
    }
*/


    /**
     * Método que busca los elementos de la vista
     * @author Domingo Lopez
     * @param view
     */
    private void findViews(View view) {

    }


    /**
     * Método que añade observer al viewmodel para observar cambios en la lista de usuarios
     * @author Domingo Lopez
     */
    private void loadSessionsData() {

        this.sessionsListViewModel.getSessions().observe(getActivity(), new Observer<List<SessionEntity>>() {
            @Override
            public void onChanged(List<SessionEntity> sessions) {

                sessionList = sessions;
                adapter.setData(sessionList);
            }
        });





    }

    /**
     * Método llamado al clickar en un item de la lista. Es un método de la clase implementada ListItemClickListener
     * @author Domingo Lopez
     * @param position
     */
    @Override
    public void onListItemClick(int position) {


    }

    @Override
    public void onListItemClickUser(int position, String user_elegido){

        switch (user_elegido){

            case "SHOW_RESULTS":
                Intent i = new Intent(requireActivity(), SessionResultActivity.class);
                i.putExtra("session_id",this.sessionList.get(position).getSession_id());
                i.putExtra("action","VISUALIZE");
                startActivity(i);

                break;


            case "DELETE_SESSION":

                    SimpleDialogFragment dialogFragment = new SimpleDialogFragment(new OnSimpleDialogClick() {
                        @Override
                        public void onPositiveButtonClick(String description) {

                        }

                        @Override
                        public void onPositiveButtonClick() {

                            sessionsListViewModel.deteleSessionByID(sessionList.get(position).getSession_id());


                        }

                        @Override
                        public void onNegativeButtonClick() {


                        }
                    }, "DELETE_SESSION");

                    dialogFragment.show(requireActivity().getSupportFragmentManager(), null);


                break;

            default:

                if(Constants.CONNECTION_UP.equals(("SI"))) {

                    if (user_elegido == null || user_elegido.equals("")) {
                        Toast.makeText(requireActivity(), "No ha seleccionado un paciente para la sesión", Toast.LENGTH_SHORT).show();
                        return;
                    }

                    //Si el usuario contiene algo, lo comparamos con el Map que tenemos
                    this.user_selected = this.usuarios_predictivo.get(user_elegido);
                    if (user_selected != 0) {
                        int id_session_local = this.sessionList.get(position).session_id;
                        this.position_selected = position;
                        Intent intent = new Intent(this.getContext(), UploadSessionService.class);
                        intent.setAction("START_UPLOAD");
                        intent.putExtra("user_id", user_selected);
                        intent.putExtra("session_id", id_session_local);
                        intent.putExtra("receiver", this.sessionResult);
                        MyApp.getInstance().startService(intent);

                    } else {
                        Toast.makeText(requireActivity(), "Debe escribir el nombre del paciente al que pertenece la sesión", Toast.LENGTH_SHORT).show();
                    }

                }else{
                    Toast.makeText(requireActivity(), "Conexión no disponible, vuelva a iniciar sesión", Toast.LENGTH_SHORT).show();
                }


                break;
        }



    }


    public ResultReceiver sessionResult = new ResultReceiver(new Handler()) {
        @Override
        protected void onReceiveResult(int resultCode, Bundle resultData) {
            super.onReceiveResult(resultCode, resultData);
            //Broadcast /send the result code in intent service based on your logic(success/error) handle with switch
            switch (resultCode) {
                case 1: //Case correcto. Sesión subida

                    Toast.makeText(requireActivity(), "Sesión sincronizada de forma satisfactoria", Toast.LENGTH_SHORT).show();
                    int deleted_session = (int) resultData.get("deleted_session");
                    //Borramos la sesión
                    SessionEntity sesionActualizar = sessionList.get(position_selected);
                    sesionActualizar.setUser_id(user_selected);
                    sesionActualizar.setSync(true);
                    sesionActualizar.setCrashed(false);
                    sessionsListViewModel.udpateSession(sesionActualizar);
                    //sessionsListViewModel.refreshSessions();

                    break;

                //Error al descargar a csv la sesión
                case 400:

                    break;

                //Error al subir la sesión
                case 401:
                    Toast.makeText(requireActivity(), "Error al subir la sesión. ¿Dispone de conexión?", Toast.LENGTH_SHORT).show();
                    break;


                //Error al subir los csv
                case 402:

                    break;

            }
        }
    };





        @Override
    public void onClick(View view) {

    }


}