package com.hdrescuer.hdrescuer.ui.ui.patienthist;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.recyclerview.widget.RecyclerView;

import com.hdrescuer.hdrescuer.R;
import com.hdrescuer.hdrescuer.common.Constants;
import com.hdrescuer.hdrescuer.db.entity.SessionEntity;
import com.hdrescuer.hdrescuer.ui.ui.patients.ListItemClickListener;

import java.lang.ref.WeakReference;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.util.Date;
import java.util.List;

/**
 * Clase RecyclerView para la lista de usuarios
 * @author Domingo Lopez
 */
public class PatientSessionListRecyclerViewAdapter extends RecyclerView.Adapter<PatientSessionListRecyclerViewAdapter.ViewHolder> {

    private List<SessionEntity> mValues;
    private Context ctx;
    final private ListItemClickListener mOnClickListener;
    final private DateFormat dateFormat;



    public PatientSessionListRecyclerViewAdapter(Context contexto, List<SessionEntity> items, ListItemClickListener onClickListener) {
        this.ctx = contexto;
        this.mValues = items;
        this.mOnClickListener = onClickListener;
        this.dateFormat = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");


    }


    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.fragment_session_hist_item, parent, false);
        return new ViewHolder(view, mOnClickListener);
    }


    @Override
    public void onBindViewHolder(final ViewHolder holder, int position) {
        if(mValues != null) {
            holder.mItem = mValues.get(position);


            holder.tvTimestampini.setText(dateFormat.format(Date.from(Instant.parse(holder.mItem.getTimestamp_ini()))));
            holder.id_session_local.setText(Integer.toString(holder.mItem.getSession_id()));
            holder.duration.setText(Constants.getHMS(holder.mItem.getTotal_time()));

            if(holder.mItem.getDescription().equals(""))
                holder.description.setText("No hay descripción para esta sesión");
            else
                holder.description.setText(holder.mItem.getDescription());


            if(!holder.mItem.isSync()){
                holder.no_connection_btn.setVisibility(View.VISIBLE);
            }else{
                holder.no_connection_btn.setVisibility(View.INVISIBLE);
            }

            if(!holder.mItem.isCrashed()){
                holder.crashed_session.setVisibility(View.INVISIBLE);
            }else{
                holder.crashed_session.setVisibility(View.VISIBLE);
            }

            if(!holder.mItem.isSync() || holder.mItem.isCrashed()){
                holder.uploadSessionHist.setVisibility(View.VISIBLE);
            }else {
                holder.uploadSessionHist.setVisibility(View.INVISIBLE);
            }

        }
    }


    public void setData(List<SessionEntity> sessions){
        this.mValues = sessions;
        notifyDataSetChanged();
    }

    /**
     * Devuelve el número de elementos en la lista de usuarios
     * @author Domingo Lopez
     * @return int
     */
    @Override
    public int getItemCount() {

        if(this.mValues != null)
            return mValues.size();
        else
            return 0;

    }


    /**
     * Clase internta para añadir el ViewHolder a cada item del RecyclerView y gestionar eventos de click en cada usuario
     *  @author Domingo Lopez
     */
    public class ViewHolder extends RecyclerView.ViewHolder implements View.OnClickListener{
        public final View mView;
        public SessionEntity mItem;

        public final TextView tvTimestampini;
        public final TextView id_session_local;
        public final TextView duration;
        public final TextView description;

        public final ImageView viewResults;
        public final ImageView deleteSession;
        public final ImageView no_connection_btn;

        public final ImageView crashed_session;

        public final Button uploadSessionHist;

        private WeakReference<ListItemClickListener> listenerRef;

        public ViewHolder(View view, ListItemClickListener listener) {
            super(view);

            //listenerRef = new WeakReference<>(listener);

            mView = view;
            tvTimestampini = view.findViewById(R.id.tvTimestampIniHIST);
            id_session_local = view.findViewById(R.id.tvSessionLocalHIST);
            duration = view.findViewById(R.id.tvDurationHIST);
            description = view.findViewById(R.id.tvDescriptionHIST);

            viewResults = view.findViewById(R.id.viewResultsLoc);
            deleteSession = view.findViewById(R.id.deleteSessionLoc);
            no_connection_btn = view.findViewById(R.id.btn_connection_lost);
            uploadSessionHist = view.findViewById(R.id.btnUploadSessionHist);

            crashed_session = view.findViewById(R.id.btn_crashed);

            //Seteamos el listener para cada botón del holder
            viewResults.setOnClickListener(this);
            deleteSession.setOnClickListener(this);
            no_connection_btn.setOnClickListener(this);
            uploadSessionHist.setOnClickListener(this);
            crashed_session.setOnClickListener(this);

            view.setOnClickListener(this);

        }

        @Override
        public String toString() {
            return super.toString();
        }

        @Override
        public void onClick(View v) {

            int position = getAdapterPosition();

            switch (v.getId()){
                case R.id.viewResultsLoc:

                    mOnClickListener.onListItemClickUser(position, "SHOW_RESULTS");
                    break;

                case R.id.deleteSessionLoc:
                    mOnClickListener.onListItemClickUser(position, "DELETE_SESSION");
                    break;

                case R.id.btn_connection_lost:
                    Toast.makeText(ctx, "Sesión no sincronizada con el servidor", Toast.LENGTH_SHORT).show();
                    break;

                case R.id.btnUploadSessionHist:
                    mOnClickListener.onListItemClickUser(position, "UPLOAD_SESSION");
                    break;

                case R.id.btn_crashed:
                    Toast.makeText(ctx, "Se perdieron datos en la emisión de la sesión. Sincronízela", Toast.LENGTH_SHORT).show();
                    break;

            }

        }
    }
}