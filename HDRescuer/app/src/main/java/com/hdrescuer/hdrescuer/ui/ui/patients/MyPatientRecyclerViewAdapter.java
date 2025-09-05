package com.hdrescuer.hdrescuer.ui.ui.patients;

import androidx.recyclerview.widget.RecyclerView;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import com.hdrescuer.hdrescuer.R;
import com.hdrescuer.hdrescuer.common.Constants;
import com.hdrescuer.hdrescuer.retrofit.response.User;


import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.util.Date;
import java.util.List;

/**
 * Clase RecyclerView para la lista de usuarios
 * @author Domingo Lopez
 */
public class MyPatientRecyclerViewAdapter extends RecyclerView.Adapter<MyPatientRecyclerViewAdapter.ViewHolder> {

    private List<User> mValues;
    private Context ctx;
    final private ListItemClickListener mOnClickListener;
    final private DateFormat dateFormat;

    public MyPatientRecyclerViewAdapter(Context contexto, List<User> items, ListItemClickListener onClickListener) {
        this.ctx = contexto;
        this.mValues = items;
        this.mOnClickListener = onClickListener;
        this.dateFormat = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");
    }

    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.fragment_user, parent, false);
        return new ViewHolder(view);
    }

    /**
     * Método que se llama para cada item de la lista, para "bindearlo" con la interfaz definiendo cada campo
     * @author Domingo Lopez
     * @param holder
     * @param position
     */
    @Override
    public void onBindViewHolder(final ViewHolder holder, int position) {
        if(mValues != null) {
            holder.mItem = mValues.get(position);

            holder.user_name.setText(holder.mItem.getUsername() + " " +holder.mItem.getLastname());

            if(holder.mItem.getTimestamp_ini() != null) {

                holder.last_monitoring.setText(dateFormat.format(Date.from(Instant.parse(holder.mItem.getTimestamp_ini()))));

            }
            else
                holder.last_monitoring.setText("- -");

            if(holder.mItem.getTotal_time() != 0)
                holder.sesion_duration.setText(Constants.getHMS(holder.mItem.getTotal_time()));
            else
                holder.sesion_duration.setText("- -");
        }
    }

    /**
     * Método que setea los usuarios de la lista y notifica a los observadores de que han cambiado los usuarios
     * @author Domingo Lopez
     * @param users
     */
    public void setData(List<User> users){
        this.mValues = users;
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
        public final TextView user_name;
        public final TextView last_monitoring;
        public final TextView sesion_duration;
        public User mItem;

        public ViewHolder(View view) {
            super(view);
            mView = view;
            user_name = (TextView) view.findViewById(R.id.textViewUserName);
            last_monitoring = (TextView) view.findViewById(R.id.tvLastSession);
            sesion_duration = (TextView) view.findViewById(R.id.tvTotalTime);

            view.setOnClickListener(this);
        }

        @Override
        public String toString() {
            return super.toString() + " '" + user_name.getText() + "'";
        }

        @Override
        public void onClick(View v) {
            int position = getAdapterPosition();
            mOnClickListener.onListItemClick(position);
        }
    }
}