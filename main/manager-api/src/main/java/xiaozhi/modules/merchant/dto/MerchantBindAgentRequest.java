package xiaozhi.modules.merchant.dto;

import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
public class MerchantBindAgentRequest {

    private Long merchantId;

    private List<String> agentIds;
}
