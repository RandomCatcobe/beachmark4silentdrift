import com.google.gson.Gson;

public class Probe {
    enum Mode {
        VALUE;

        @Override
        public String toString() {
            return "wire";
        }
    }

    public static void main(String[] args) {
        Mode mode = new Gson().fromJson("\"wire\"", Mode.class);
        System.out.println(mode == null ? "null" : mode.name());
    }
}
