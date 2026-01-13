package xiaozhi.modules.merchant;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.EqualsAndHashCode;

import java.util.Date;

/**
 * 表名：ai_merchant
 * 表注释：商户表
*/
@EqualsAndHashCode(callSuper = false)
@TableName("ai_merchant")
@Schema(description = "设备信息")
public class MerchantEntity {
    /**
     * id
     */
    @TableId(type = IdType.AUTO)
    @Schema(description = "ID")
    private Long id;

    /**
     * 商户名称
     */
    private String name;

    /**
     * 状态  0：停用   1：正常
     */
    private Byte status;

    /**
     * 创建时间
     */
    private Date createDate;

    /**
     * 更新者
     */
    private Long updater;

    /**
     * 创建者
     */
    private Long creator;

    /**
     * 更新时间
     */
    private Date updateDate;

    /**
     * 获取id
     *
     * @return id - id
     */
    public Long getId() {
        return id;
    }

    /**
     * 设置id
     *
     * @param id id
     */
    public void setId(Long id) {
        this.id = id;
    }

    /**
     * 获取商户名称
     *
     * @return name - 商户名称
     */
    public String getName() {
        return name;
    }

    /**
     * 设置商户名称
     *
     * @param name 商户名称
     */
    public void setName(String name) {
        this.name = name;
    }

    /**
     * 获取状态  0：停用   1：正常
     *
     * @return status - 状态  0：停用   1：正常
     */
    public Byte getStatus() {
        return status;
    }

    /**
     * 设置状态  0：停用   1：正常
     *
     * @param status 状态  0：停用   1：正常
     */
    public void setStatus(Byte status) {
        this.status = status;
    }

    /**
     * 获取创建时间
     *
     * @return createDate - 创建时间
     */
    public Date getCreateDate() {
        return createDate;
    }

    /**
     * 设置创建时间
     *
     * @param createDate 创建时间
     */
    public void setCreateDate(Date createDate) {
        this.createDate = createDate;
    }

    /**
     * 获取更新者
     *
     * @return updater - 更新者
     */
    public Long getUpdater() {
        return updater;
    }

    /**
     * 设置更新者
     *
     * @param updater 更新者
     */
    public void setUpdater(Long updater) {
        this.updater = updater;
    }

    /**
     * 获取创建者
     *
     * @return creator - 创建者
     */
    public Long getCreator() {
        return creator;
    }

    /**
     * 设置创建者
     *
     * @param creator 创建者
     */
    public void setCreator(Long creator) {
        this.creator = creator;
    }

    /**
     * 获取更新时间
     *
     * @return updateDate - 更新时间
     */
    public Date getUpdateDate() {
        return updateDate;
    }

    /**
     * 设置更新时间
     *
     * @param updateDate 更新时间
     */
    public void setUpdateDate(Date updateDate) {
        this.updateDate = updateDate;
    }
}